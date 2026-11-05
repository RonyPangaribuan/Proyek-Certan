"""Run preregistered v2 study; never write labels, protocol or legacy outputs.

Calibration uses development queries only. Evaluation is scored once with
frozen rules and thresholds. All ranking scores retain separate raw cosines.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from math import sqrt
from pathlib import Path

import numpy as np
from benchmark_semantic_retrieval import average, metrics
from build_reviewed_corpus import check_store
from metadata_intent_candidate import BONUS, query_intent, rank_documents

from proyek_certan.knowledge.embeddings import EmbeddingModel
from proyek_certan.knowledge.models import validate_chunks
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore

ROOT = Path(__file__).resolve().parents[1]
METRICS = [f"{m}@{k}" for m in ("recall", "precision") for k in (1, 3, 5)] + ["mrr"]
ARCHIVED_RULE_PATHS = {
    "src/proyek_certan/knowledge/intent_experiment.py": "evaluation/metadata_intent_candidate.py",
}


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rule_path(original: str) -> Path:
    """Failed candidate archived outside runtime, with original bytes unchanged.

    Preserve the preregistration file as history; this explicit relocation does
    not permit rule changes because the original SHA-256 is still required.
    """
    return ROOT / ARCHIVED_RULE_PATHS.get(original, original)


def wilson(errors: int, count: int) -> list[float] | None:
    if not count:
        return None
    z = 1.959963984540054
    p = errors / count
    denom = 1 + z * z / count
    centre = (p + z * z / (2 * count)) / denom
    margin = z * sqrt(p * (1 - p) / count + z * z / (4 * count * count)) / denom
    return [max(0.0, centre - margin), min(1.0, centre + margin)]


def summary(rows: list[dict], threshold: float | None = None) -> dict:
    positive = [r for r in rows if r["relevant_documents"]]
    ood = [r for r in rows if not r["relevant_documents"]]

    def accepted(row):
        return bool(row["documents"]) and (
            threshold is None or row["documents"][0]["similarity"] >= threshold
        )

    fa = [r["id"] for r in ood if accepted(r)]
    fr = [r["id"] for r in positive if not accepted(r)]
    scores = [
        metrics(
            [d["document_id"] for d in r["documents"]] if accepted(r) else [],
            set(r["relevant_documents"]),
        )
        for r in positive
    ]
    accepted_pos = [r for r in positive if accepted(r)]
    wrong = [
        r["id"]
        for r in accepted_pos
        if r["documents"][0]["document_id"] not in r["relevant_documents"]
    ]
    far = len(fa) / len(ood) if ood else None
    frr = len(fr) / len(positive) if positive else None
    by_distance = {}
    for distance in ("near", "far"):
        subset = [r for r in ood if r.get("ood_distance") == distance]
        if subset:
            n = sum(accepted(r) for r in subset)
            by_distance[distance] = {
                "count": len(subset),
                "false_accept_count": n,
                "rate": n / len(subset),
                "wilson95": wilson(n, len(subset)),
            }
    return {
        "metrics": {key: average(scores, key) for key in METRICS},
        "positive_count": len(positive),
        "ood_count": len(ood),
        "threshold": threshold,
        "false_acceptance_count": len(fa),
        "false_acceptance_rate": far,
        "false_acceptance_ids": fa,
        "false_acceptance_wilson95": wilson(len(fa), len(ood)),
        "false_rejection_count": len(fr),
        "false_rejection_rate": frr,
        "false_rejection_ids": fr,
        "false_rejection_wilson95": wilson(len(fr), len(positive)),
        "balanced_error": (far + frr) / 2
        if far is not None and frr is not None
        else None,
        "accepted_positive_count": len(accepted_pos),
        "accepted_wrong_top1_ids": wrong,
        "accepted_correct_top1_count": len(accepted_pos) - len(wrong),
        "accepted_correct_top1_fraction": (len(accepted_pos) - len(wrong))
        / (len(accepted_pos) + len(fa))
        if len(accepted_pos) + len(fa)
        else None,
        "ood_by_distance": by_distance,
    }


def select_threshold(rows: list[dict], grid: list[float]) -> tuple[float, list[dict]]:
    if not rows or any(r["split"] != "development" for r in rows):
        raise ValueError("threshold calibration accepts development queries only")
    if not any(r["relevant_documents"] for r in rows) or not any(
        not r["relevant_documents"] for r in rows
    ):
        raise ValueError("calibration needs positive and OOD queries")
    curve = [summary(rows, t) for t in grid]
    best = min(
        curve,
        key=lambda s: (s["balanced_error"], s["false_acceptance_rate"], s["threshold"]),
    )
    return best["threshold"], curve


def paired_difference(before: list[dict], after: list[dict]) -> dict:
    left = {r["id"]: r for r in before if r["relevant_documents"]}
    right = {r["id"]: r for r in after if r["relevant_documents"]}
    if set(left) != set(right):
        raise ValueError("paired comparison requires identical query IDs")
    for q in left:
        if left[q]["relevant_documents"] != right[q]["relevant_documents"]:
            raise ValueError("paired comparison requires identical relevance labels")
    rng = np.random.default_rng(20261105)
    output = {}
    for key in ("recall@3", "mrr"):
        delta = np.array(
            [right[q]["metrics"][key] - left[q]["metrics"][key] for q in left]
        )
        means = delta[rng.integers(0, len(delta), size=(10000, len(delta)))].mean(
            axis=1
        )
        output[key] = {
            "delta": float(delta.mean()),
            "bootstrap95": [float(v) for v in np.quantile(means, [0.025, 0.975])],
            "improved": int(np.sum(delta > 0)),
            "unchanged": int(np.sum(delta == 0)),
            "regressed": int(np.sum(delta < 0)),
            "regressed_ids": [q for q, d in zip(left, delta, strict=True) if d < 0],
        }
    return output


def serialise(result, rank: int, intent: str | None = None) -> dict:
    m = result.metadata
    return {
        "rank": rank,
        "chunk_id": result.chunk_id,
        "document_id": m["document_id"],
        "similarity": result.similarity,
        "ranking_score": result.similarity
        + (BONUS if intent and m.get("document_kind") == intent else 0.0),
        "section": m.get("section"),
        "document_kind": m.get("document_kind"),
        "source_url": m.get("source_url"),
        "review_required": m.get("review_required"),
        "publication_status": m.get("publication_status"),
    }


def rows_for(queries, raw, candidate=False):
    rows = []
    for q, found in zip(queries, raw, strict=True):
        ranked = rank_documents(found, query=q["query"] if candidate else None)
        intent = query_intent(q["query"]) if candidate else None
        documents = [serialise(r, i, intent) for i, r in enumerate(ranked, 1)]
        if len(documents) < 5:
            raise ValueError(f"insufficient distinct documents for {q['id']}")
        rows.append(
            dict(
                **q,
                intent=intent,
                documents=documents,
                metrics=metrics(
                    [d["document_id"] for d in documents], set(q["relevant_documents"])
                ),
            )
        )
    return rows


def analyse(rows, grid):
    splits = {
        s: [r for r in rows if r["split"] == s]
        for s in ("legacy", "development", "evaluation")
    }
    threshold, curve = select_threshold(splits["development"], grid)
    return {
        "selected_threshold": threshold,
        "development_threshold_curve": curve,
        "splits": {
            s: {
                "ungated": summary(rr),
                "gated": summary(rr, threshold),
                "by_category": {
                    c: summary([r for r in rr if r["category"] == c])
                    for c in sorted({r["category"] for r in rr})
                },
            }
            for s, rr in splits.items()
        },
    }


def run() -> dict:
    protocol = read("evaluation/retrieval_study_protocol_v2.json")
    labels = read("evaluation/retrieval_study_labels_v2.json")
    if (
        sha(ROOT / "evaluation/retrieval_study_labels_v2.json")
        != protocol["labels_sha256"]
    ):
        raise ValueError("frozen labels changed")
    for path, expected in protocol["frozen_baseline_sha256"].items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"frozen baseline changed: {path}")
    for key in ("rules", "metadata_rule"):
        if (
            sha(rule_path(protocol["candidate"][f"{key}_file"]))
            != protocol["candidate"][f"{key}_sha256"]
        ):
            raise ValueError("preregistered candidate code changed")
    legacy = read("evaluation/semantic_retrieval_ground_truth.json")["queries"]
    queries = [dict(**q, split="legacy", category=q["type"]) for q in legacy] + labels[
        "queries"
    ]
    if len({q["id"] for q in queries}) != len(queries) or len(
        {q["query"] for q in queries}
    ) != len(queries):
        raise ValueError("duplicate queries/IDs")
    corpus = read("evaluation/reviewed_corpus_v2.json")
    old = read("evaluation/token_chunking_comparison.json")["profiles"]["t96_w10"]
    profiles = {"v1_t96_w10": old, **corpus["profiles"]}
    embedder = EmbeddingModel()
    vectors = embedder.encode([q["query"] for q in queries])

    class CachedQueries:
        model_name = embedder.model_name

        def encode(self, text):
            return vectors[
                [next(i for i, q in enumerate(queries) if q["query"] == text)]
            ]

    output = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "labels_sha256": protocol["labels_sha256"],
        "protocol_sha256": sha(ROOT / "evaluation/retrieval_study_protocol_v2.json"),
        "corpus_report_sha256": sha(ROOT / "evaluation/reviewed_corpus_v2.json"),
        "model_name": embedder.model_name,
        "raw_depth": protocol["raw_depth"],
        "metric_scope": "Distinct documents in top 100 chunks. Ungated ranking and gated metrics reported separately. Rejected positive queries contribute zeros to gated Recall/Precision/MRR.",
        "arms": {},
    }
    for name, profile in profiles.items():
        cp = ROOT / profile["chunk_file"]
        if sha(cp) != profile["chunk_file_sha256"]:
            raise ValueError("chunk SHA mismatch")
        chunks = validate_chunks(json.loads(cp.read_text(encoding="utf-8")))
        with VectorStore(ROOT / profile["database_path"]) as store:
            check_store(store, chunks)
            retriever = KnowledgeRetriever(store, CachedQueries())
            raw = [
                retriever.search(q["query"], top_k=protocol["raw_depth"])
                for q in queries
            ]
        arms = [(name, False)]
        if name == "v2_t96_w10":
            arms.append(("v2_t96_w10_intent", True))
        raw_ranking = {
            q["id"]: [serialise(r, i) for i, r in enumerate(found, 1)]
            for q, found in zip(queries, raw, strict=True)
        }
        for arm, candidate in arms:
            rows = rows_for(queries, raw, candidate)
            output["arms"][arm] = dict(
                profile=name,
                candidate=candidate,
                chunk_count=profile["chunk_count"],
                database_path=profile["database_path"],
                chunk_file_sha256=profile["chunk_file_sha256"],
                queries=rows,
                raw_chunk_ranking=raw_ranking
                if not candidate
                else "shared with v2_t96_w10",
                **analyse(rows, protocol["threshold_grid"]),
            )
            print(
                arm,
                json.dumps(
                    {
                        s: {
                            "ungated": r["ungated"]["metrics"],
                            "threshold": output["arms"][arm]["selected_threshold"],
                            "fa": r["gated"]["false_acceptance_count"],
                            "fr": r["gated"]["false_rejection_count"],
                        }
                        for s, r in output["arms"][arm]["splits"].items()
                    }
                ),
                flush=True,
            )
    output["paired_comparisons"] = {}
    for before, after in (
        ("v1_t96_w10", "v2_t96_w10"),
        ("v2_t96_w10", "v2_t96_w10_intent"),
        ("v2_t96_w0", "v2_t96_w10"),
        ("v2_t120_w12", "v2_t96_w10"),
    ):
        output["paired_comparisons"][f"{before}__{after}"] = {
            s: paired_difference(
                [r for r in output["arms"][before]["queries"] if r["split"] == s],
                [r for r in output["arms"][after]["queries"] if r["split"] == s],
            )
            for s in ("legacy", "development", "evaluation")
        }
    contrast = output["paired_comparisons"]["v2_t96_w10__v2_t96_w10_intent"]
    strong = all(
        contrast[s][m]["bootstrap95"][0] > 0
        for s in ("development", "evaluation")
        for m in ("recall@3", "mrr")
    )
    no_error_increase = all(
        output["arms"]["v2_t96_w10_intent"]["splits"][s]["gated"][m]
        <= output["arms"]["v2_t96_w10"]["splits"][s]["gated"][m]
        for s in ("development", "evaluation")
        for m in ("false_acceptance_rate", "false_rejection_rate")
    )
    output["candidate_decision"] = {
        "adopt": strong and no_error_increase,
        "confidence_rule_met": strong,
        "error_non_regression_met": no_error_increase,
        "default": "semantic",
        "reason": "Default remains semantic unless ALL preregistered adoption conditions pass. Failed candidate code archived under evaluation only, never imported by the production package.",
        "archived_rule_paths": ARCHIVED_RULE_PATHS,
    }
    output["wifi_case"] = {}
    for name, arm in output["arms"].items():
        row = next(r for r in arm["queries"] if r["id"] == "wifi_diagnosis")
        output["wifi_case"][name] = {
            "query": row["query"],
            "top_documents": row["documents"][:7],
            "ranks": {
                d["document_id"]: d["rank"]
                for d in row["documents"]
                if d["document_id"] in {"DOC01", "DOC13"}
            },
        }
    path = ROOT / "evaluation/retrieval_study_results_v2.json"
    path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output


if __name__ == "__main__":
    run()
