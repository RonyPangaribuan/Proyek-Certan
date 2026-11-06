"""Immutable observations, development-only selection, validation and one final test.

Historical files are read only. Every output is create-once. The final test
must be authored AFTER lock-r2.json; running it never changes selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from time import perf_counter

import numpy as np
from benchmark_semantic_retrieval import metrics
from build_reviewed_corpus import check_store
from retrieval_study import wilson
from title_candidate_v3 import rank_titles

from proyek_certan.knowledge.documents import (
    CorpusCatalog,
    DocumentResult,
    distinct_documents,
)
from proyek_certan.knowledge.embeddings import EmbeddingModel
from proyek_certan.knowledge.models import validate_chunks
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.scope import GuardConfig, ScopeGuard
from proyek_certan.knowledge.vector_store import VectorStore

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/quality-v3"
METRICS = ("precision@1", "precision@3", "recall@3", "recall@5", "mrr")
CODE = [
    "src/proyek_certan/knowledge/documents.py",
    "src/proyek_certan/knowledge/scope.py",
    "src/proyek_certan/knowledge/retrieval.py",
    "src/proyek_certan/knowledge/cli.py",
    "evaluation/title_candidate_v3.py",
    "evaluation/quality_v3.py",
]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(UTC).isoformat()


def write_once(path, value):
    path = Path(path)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def verify_baseline():
    protocol = read(OUT / "protocol.json")
    for p, h in protocol["baseline_sha256"].items():
        if sha(ROOT / p) != h:
            raise ValueError(f"Historical baseline changed: {p}")
    for s in ("development", "validation"):
        if sha(OUT / f"{s}.json") != protocol[f"{s}_sha256"]:
            raise ValueError("Labels changed")
    return protocol


def collect(split, corpus_path):
    verify_baseline()
    output = OUT / f"observations_{split}.json"
    if output.exists():
        raise FileExistsError(
            "Observations already frozen; do not overwrite or select retries"
        )
    if split == "final_test":
        lock = read(OUT / "lock-r2.json")
        for p, h in lock["code_sha256"].items():
            if sha(ROOT / p) != h:
                raise ValueError("Candidate code changed after lock")
        manifest = read(OUT / "final_test_manifest.json")
        if manifest["lock_sha256"] != sha(OUT / "lock-r2.json") or manifest[
            "labels_sha256"
        ] != sha(OUT / "final_test.json"):
            raise ValueError("Final test freeze mismatch")
        if sha(corpus_path) != lock["corpus_report_sha256"]:
            raise ValueError("Final corpus changed")
    corpus = read(corpus_path)
    profile = corpus["profiles"][
        next(n for n in corpus["profiles"] if n.endswith("t96_w10"))
    ]
    if sha(ROOT / profile["chunk_file"]) != profile["chunk_file_sha256"]:
        raise ValueError("Chunk hash mismatch")
    chunks = validate_chunks(read(ROOT / profile["chunk_file"]))
    labels = read(OUT / f"{split}.json")["queries"]
    embedder = EmbeddingModel()
    started = perf_counter()
    dimension = embedder.dimension
    cold = (perf_counter() - started) * 1000
    rows = []
    with VectorStore(ROOT / profile["database_path"]) as store:
        check_store(store, chunks)
        retriever = KnowledgeRetriever(store, embedder)
        # Warm caches without using a labelled evaluation query.
        retriever.search("Panduan umum jaringan komputer", top_k=5)
        retriever.title_scores("Panduan umum jaringan komputer")
        for label in labels:
            start = perf_counter()
            raw = retriever.search(label["query"], top_k=100)
            dense_ms = (perf_counter() - start) * 1000
            start = perf_counter()
            docs = distinct_documents(raw)
            dedup_ms = (perf_counter() - start) * 1000
            start = perf_counter()
            titles = retriever.title_scores(label["query"])
            title_ms = (perf_counter() - start) * 1000
            rows.append(
                dict(
                    **label,
                    documents=[asdict(d) for d in docs],
                    title_scores=titles,
                    latency_ms=dict(dense=dense_ms, dedup=dedup_ms, title=title_ms),
                )
            )
    value = dict(
        generated_at_utc=now(),
        split=split,
        labels_sha256=sha(OUT / f"{split}.json"),
        corpus_report=str(Path(corpus_path).relative_to(ROOT)).replace("\\", "/"),
        corpus_report_sha256=sha(corpus_path),
        chunk_file_sha256=profile["chunk_file_sha256"],
        database_path=profile["database_path"],
        embedding_dimension=dimension,
        cold_model_load_ms=cold,
        latency_scope="One warmed observation per query; model/title caches warmed; no latency significance claim.",
        queries=rows,
    )
    write_once(output, value)
    print("Collected", split, len(rows), "queries", flush=True)
    return value


def evaluate(observations, *, guard=None, alpha=None):
    corpus = read(ROOT / observations["corpus_report"])
    catalog = CorpusCatalog(
        [
            dict(
                document_id=d["document_id"], title=d["title"], publisher=d["publisher"]
            )
            for d in corpus["documents"]
        ]
    )
    rows = []
    for q in observations["queries"]:
        docs = [DocumentResult(**d) for d in q["documents"]]
        start = perf_counter()
        if alpha is not None:
            docs = rank_titles(docs, q["title_scores"], alpha)
        ranking_ms = (perf_counter() - start) * 1000
        support = max(
            (q["title_scores"][d.document_id] for d in docs[:3]), default=None
        )
        if guard is not None and guard["support_threshold"] <= 0:
            support = None
        start = perf_counter()
        if guard is not None:
            decision = ScopeGuard(GuardConfig(**guard)).evaluate(
                q["query"], docs, title_support=support, catalog=catalog
            )
            status = decision.status
            reasons = list(decision.reason_codes)
            explanation = list(decision.reasons)
        else:
            status = (
                "ACCEPT" if docs and docs[0].similarity >= 0.5 else "LOW_CONFIDENCE"
            )
            reasons = ["cosine_only_baseline"]
            explanation = ["Baseline gate uses raw selected-document cosine >= 0.5."]
        gate_ms = (perf_counter() - start) * 1000
        ranked = [d.document_id for d in docs]
        relevant = set(q["relevant_documents"])
        rows.append(
            dict(
                id=q["id"],
                query=q["query"],
                category=q["category"],
                relevant_documents=q["relevant_documents"],
                evidence=q["evidence"],
                status=status,
                reason_codes=reasons,
                reasons=explanation,
                title_support=support,
                documents=[asdict(d) for d in docs[:7]],
                ungated=metrics(ranked, relevant),
                gated=metrics(ranked if status == "ACCEPT" else [], relevant),
                latency_ms=q["latency_ms"]["dense"]
                + q["latency_ms"]["dedup"]
                + ranking_ms
                + gate_ms
                + (
                    q["latency_ms"]["title"]
                    if (guard is not None and guard["support_threshold"] > 0)
                    or alpha is not None
                    else 0
                ),
            )
        )
    return rows


def summarize(rows):
    pos = [r for r in rows if r["relevant_documents"]]
    ood = [r for r in rows if not r["relevant_documents"]]
    fa = sum(r["status"] == "ACCEPT" for r in ood)
    fr = sum(r["status"] != "ACCEPT" for r in pos)
    output = dict(
        positive_count=len(pos),
        ood_count=len(ood),
        false_acceptance_count=fa,
        false_rejection_count=fr,
        far=fa / len(ood) if ood else None,
        frr=fr / len(pos) if pos else None,
        far_wilson95=wilson(fa, len(ood)),
        frr_wilson95=wilson(fr, len(pos)),
        ood_rejection_rate=1 - fa / len(ood) if ood else None,
        positive_acceptance_rate=1 - fr / len(pos) if pos else None,
        decisions={
            s: sum(r["status"] == s for r in rows)
            for s in ("ACCEPT", "ABSTAIN", "LOW_CONFIDENCE")
        },
        false_acceptance_ids=[r["id"] for r in ood if r["status"] == "ACCEPT"],
        false_rejection_ids=[r["id"] for r in pos if r["status"] != "ACCEPT"],
        wrong_top1_ids=[
            r["id"]
            for r in pos
            if r["status"] == "ACCEPT"
            and r["documents"][0]["document_id"] not in r["relevant_documents"]
        ],
        latency_ms=dict(
            median=median(r["latency_ms"] for r in rows),
            p95=float(np.quantile([r["latency_ms"] for r in rows], 0.95)),
        ),
    )
    for mode in ("ungated", "gated"):
        output[mode] = {
            m: sum(r[mode][m] for r in pos) / len(pos) if pos else None for m in METRICS
        }
    return output


def paired(before, after):
    if [r["id"] for r in before] != [r["id"] for r in after]:
        raise ValueError("Unpaired query sets")
    for a, b in zip(before, after, strict=True):
        if a["relevant_documents"] != b["relevant_documents"]:
            raise ValueError("Different ground truth")
    rng = np.random.default_rng(20261106)
    result = {}
    for name in (
        *METRICS,
        "far",
        "frr",
        "ungated_mrr",
        "ungated_precision@1",
        "ungated_recall@3",
    ):
        differences = []
        for a, b in zip(before, after, strict=True):
            positive = bool(a["relevant_documents"])
            if name == "far" and not positive:
                delta = int(b["status"] == "ACCEPT") - int(a["status"] == "ACCEPT")
            elif name == "frr" and positive:
                delta = int(b["status"] != "ACCEPT") - int(a["status"] != "ACCEPT")
            elif name.startswith("ungated_") and positive:
                delta = b["ungated"][name[8:]] - a["ungated"][name[8:]]
            elif name in METRICS and positive:
                delta = b["gated"][name] - a["gated"][name]
            else:
                continue
            differences.append(delta)
        d = np.asarray(differences)
        means = d[rng.integers(0, len(d), (10000, len(d)))].mean(axis=1)
        result[name] = dict(
            delta=float(d.mean()),
            bootstrap95=[float(v) for v in np.quantile(means, [0.025, 0.975])],
        )
    return result


def selection(corpus_path):
    p = verify_baseline()
    dev = read(OUT / "observations_development.json")
    if sha(corpus_path) != dev["corpus_report_sha256"]:
        raise ValueError("Corpus differs from development observations")
    baseline = evaluate(dev)
    bs = summarize(baseline)
    curve = []
    for t in p["threshold_grid"]:
        for support in p["support_grid"]:
            config = dict(similarity_threshold=t, support_threshold=support)
            summary = summarize(evaluate(dev, guard=config))
            curve.append(dict(config=config, summary=summary))
    eligible = [r for r in curve if r["summary"]["frr"] <= bs["frr"] + 1 / 18 + 1e-12]
    selected = min(
        eligible,
        key=lambda r: (
            (r["summary"]["far"] + r["summary"]["frr"]) / 2,
            r["summary"]["far"],
            r["config"]["similarity_threshold"],
            r["config"]["support_threshold"],
        ),
    )
    alphas = []
    for alpha in (0.2, 0.4, 0.6):
        alphas.append(dict(alpha=alpha, summary=summarize(evaluate(dev, alpha=alpha))))
    chosen = max(
        alphas,
        key=lambda r: (
            r["summary"]["ungated"]["precision@1"],
            r["summary"]["ungated"]["mrr"],
            r["summary"]["ungated"]["recall@3"],
            -r["alpha"],
        ),
    )
    lock = dict(
        locked_at_utc=now(),
        protocol_sha256=sha(OUT / "protocol.json"),
        corpus_report_sha256=sha(corpus_path),
        code_sha256={file: sha(ROOT / file) for file in CODE},
        development_observations_sha256=sha(OUT / "observations_development.json"),
        guard_config=selected["config"],
        title_alpha=chosen["alpha"],
        development_guard_grid=curve,
        development_title_grid=alphas,
    )
    write_once(OUT / "lock-r2.json", lock)
    print(
        "LOCKED guard",
        lock["guard_config"],
        "alpha",
        lock["title_alpha"],
        "before final test exists",
        flush=True,
    )


def report(split):
    verify_baseline()
    lock = read(OUT / "lock-r2.json")
    for p, h in lock["code_sha256"].items():
        if sha(ROOT / p) != h:
            raise ValueError(f"Locked implementation changed: {p}")
    observations = read(OUT / f"observations_{split}.json")
    arms = {
        "baseline": evaluate(observations),
        "guard": evaluate(observations, guard=lock["guard_config"]),
        "title": evaluate(observations, alpha=lock["title_alpha"]),
        "title_guard": evaluate(
            observations, guard=lock["guard_config"], alpha=lock["title_alpha"]
        ),
    }
    comparisons = {
        n: paired(arms["baseline"], r) for n, r in arms.items() if n != "baseline"
    }
    value = dict(
        generated_at_utc=now(),
        split=split,
        lock_sha256=sha(OUT / "lock-r2.json"),
        observations_sha256=sha(OUT / f"observations_{split}.json"),
        arms={
            n: dict(
                summary=summarize(rows),
                by_category={
                    c: summarize([r for r in rows if r["category"] == c])
                    for c in sorted({r["category"] for r in rows})
                },
                queries=rows,
            )
            for n, rows in arms.items()
        },
        comparisons=comparisons,
    )
    suffix = "_r2" if split == "development" else ""
    write_once(OUT / f"results_{split}{suffix}.json", value)
    for n, arm in value["arms"].items():
        print(split, n, json.dumps(arm["summary"]), flush=True)
    return value


def decision():
    verify_baseline()
    reports = [read(OUT / f"results_{s}.json") for s in ("validation", "final_test")]
    guard_ok = all(
        r["comparisons"]["guard"]["far"]["bootstrap95"][1] < 0
        and r["comparisons"]["guard"]["frr"]["delta"] <= 0.0556
        and all(
            r["comparisons"]["guard"][m]["delta"] >= -0.0556
            for m in ("precision@1", "recall@3", "mrr")
        )
        for r in reports
    )
    ranking_ok = all(
        r["comparisons"]["title"]["ungated_mrr"]["bootstrap95"][0] > 0
        and r["comparisons"]["title"]["ungated_precision@1"]["delta"] >= 0
        and r["comparisons"]["title"]["ungated_recall@3"]["delta"] >= 0
        for r in reports
    )
    value = dict(
        decided_at_utc=now(),
        guard_adopted=guard_ok,
        title_ranking_adopted=ranking_ok,
        guard_config=read(OUT / "lock-r2.json")["guard_config"],
        note="Validation and final test may veto adoption; no threshold or candidate changes from these results. Semantic chunk default remains backward-compatible; document and guard modes require explicit opt-in.",
    )
    write_once(OUT / "decision.json", value)
    print(json.dumps(value, indent=2))
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("collect", "lock", "report", "decide"))
    parser.add_argument("--split", choices=("development", "validation", "final_test"))
    parser.add_argument(
        "--corpus", type=Path, default=ROOT / "evaluation/reviewed_corpus_v3.json"
    )
    args = parser.parse_args()
    if args.stage == "collect":
        collect(args.split, args.corpus)
    elif args.stage == "lock":
        selection(args.corpus)
    elif args.stage == "report":
        report(args.split)
    else:
        decision()
