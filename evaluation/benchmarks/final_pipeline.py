"""Verify active artifacts, replay frozen baseline metrics, and run live regressions.

No experimental runner imports, label authoring, or final-test tuning. Without
--live no model/database is opened. Outputs are create-once receipts.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
from time import perf_counter

from proyek_certan.knowledge.final_corpus import REPOSITORY_ROOT, load_final_corpus, sha256, verify_index


ROOT = REPOSITORY_ROOT
K_VALUES = (1, 3, 5)


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def metrics(ranked_documents, relevant):
    """Document-level precision/recall and MRR; OOD recall/MRR are undefined."""
    ranked = list(dict.fromkeys(ranked_documents))
    result = {}
    for k in K_VALUES:
        hits = sum(doc in relevant for doc in ranked[:k])
        result[f"recall@{k}"] = hits / len(relevant) if relevant else None
        result[f"precision@{k}"] = hits / k
    result["mrr"] = next((1 / rank for rank, doc in enumerate(ranked, 1) if doc in relevant), 0.0) if relevant else None
    return result


def ood_metrics(rows, threshold):
    positive = [q for q in rows if q["relevant_documents"]]
    negative = [q for q in rows if not q["relevant_documents"]]
    fa = sum(q["top1_similarity"] >= threshold for q in negative)
    fr = sum(q["top1_similarity"] < threshold for q in positive)
    rejected_ood = len(negative) - fa
    return dict(threshold=threshold, positive_count=len(positive), ood_count=len(negative),
                false_acceptance_count=fa, false_rejection_count=fr,
                far=fa / len(negative) if negative else None,
                frr=fr / len(positive) if positive else None,
                rejection_precision=rejected_ood / (rejected_ood + fr) if rejected_ood + fr else None,
                ood_rejection_rate=rejected_ood / len(negative) if negative else None)


def summarize(rows):
    positive = [q for q in rows if q["relevant_documents"]]
    return {key: sum(q["metrics"][key] for q in positive) / len(positive) if positive else None
            for key in (f"{name}@{k}" for name in ("precision", "recall") for k in K_VALUES)} | {
                "mrr": sum(q["metrics"]["mrr"] for q in positive) / len(positive) if positive else None}


def verify_history():
    evidence = read("evaluation/evidence.json")
    for entry in evidence["preserved_files"]:
        if sha256(ROOT / entry["path"]) != entry["sha256"]:
            raise ValueError(f"Frozen evidence changed: {entry['path']}")
    observations = read("evaluation/quality-v3/observations_final_test.json")
    report = read("evaluation/quality-v3/results_final_test.json")
    labels_path = "evaluation/quality-v3/final_test.json"
    if (sha256(ROOT / labels_path) != observations["labels_sha256"]
            or sha256(ROOT / "evaluation/quality-v3/observations_final_test.json") != report["observations_sha256"]):
        raise ValueError("Frozen observation linkage mismatch")
    labels = read(labels_path)["queries"]
    baseline = report["arms"]["baseline"]
    rows = []
    for label, observation, saved in zip(labels, observations["queries"], baseline["queries"], strict=True):
        if not label["id"] == observation["id"] == saved["id"]:
            raise ValueError("Frozen query alignment mismatch")
        ranked = [d["document_id"] for d in observation["documents"]]
        calculated = metrics(ranked, set(label["relevant_documents"]))
        if calculated != saved["ungated"]:
            raise ValueError(f"Frozen metric replay mismatch: {label['id']}")
        rows.append(dict(**label, metrics=calculated,
                         top1_similarity=observation["documents"][0]["similarity"]))
    summary = summarize(rows)
    for key, value in baseline["summary"]["ungated"].items():
        if abs(summary[key] - value) > 1e-12:
            raise ValueError(f"Frozen summary mismatch: {key}")
    gate = ood_metrics(rows, 0.5)
    for key in ("false_acceptance_count", "false_rejection_count", "far", "frr"):
        if gate[key] != baseline["summary"][key]:
            raise ValueError(f"Frozen gate mismatch: {key}")
    return dict(status="PASS", method="Arithmetic replay of original baseline observations; no retrieval rerun",
                files_checked=len(evidence["preserved_files"]), archive_tag=evidence["archive_tag"],
                final_test_baseline=summary, historical_ood_diagnostic=gate,
                rejected_candidates=read("evaluation/quality-v3/decision.json"))


def collect(retriever, labels):
    rows = []
    for label in labels:
        start = perf_counter()
        documents = retriever.search_documents(label["query"], top_k=15, candidate_depth=100)
        ranked = [d.document_id for d in documents]
        rows.append(dict(**label, ranking=ranked,
                         top1_similarity=documents[0].similarity if documents else -1.0,
                         top5=[dict(document_id=d.document_id, chunk_id=d.chunk_id, similarity=d.similarity,
                                    section=d.section) for d in documents[:5]],
                         metrics=metrics(ranked, set(label["relevant_documents"])),
                         latency_ms=(perf_counter() - start) * 1000))
    return rows


def live_benchmark(corpus):
    from proyek_certan.corpus.ingestion import build_chunks, chunk_bytes
    from proyek_certan.knowledge.embeddings import EmbeddingModel, _load_model
    from proyek_certan.knowledge.retrieval import KnowledgeRetriever
    from proyek_certan.knowledge.vector_store import VectorStore

    if not (corpus.database_path / "chroma.sqlite3").is_file():
        raise ValueError("Run final_cli index first")
    model = EmbeddingModel(cache_folder=corpus.model_cache)
    loaded = _load_model(model.model_name, model.cache_folder)
    if loaded.max_seq_length != 128:
        raise ValueError("Model input limit changed")
    rebuilt, statistics = build_chunks(ROOT, loaded.tokenizer)
    if chunk_bytes(rebuilt) != (ROOT / corpus.manifest["chunks"]["path"]).read_bytes():
        raise ValueError("Recursive corpus is not reproducible")
    sensitivity = {"recursive_t96_w10": statistics}
    for cap, overlap in ((96, 0), (120, 12)):
        _, alternative = build_chunks(ROOT, loaded.tokenizer, cap=cap, overlap=overlap)
        sensitivity[f"recursive_t{cap}_w{overlap}"] = alternative
    with VectorStore(corpus.database_path, model_name=model.model_name) as store:
        index = verify_index(store, corpus)
        retriever = KnowledgeRetriever(store, model)
        legacy = collect(retriever, read("evaluation/semantic_retrieval_ground_truth.json")["queries"])
        development = collect(retriever, read("evaluation/quality-v3/development.json")["queries"])
        # A declared grid and development-only criterion; evaluation never changes it.
        choices = [ood_metrics(development, step / 20) for step in range(21)]
        feasible = [q for q in choices if q["false_rejection_count"] <= 1]
        chosen = min(feasible, key=lambda q: (q["far"], q["frr"], q["threshold"]))
        splits = dict(legacy=legacy, development=development)
        for split in ("validation", "final_test"):
            splits[split] = collect(retriever, read(f"evaluation/quality-v3/{split}.json")["queries"])
    output = {}
    for split, rows in splits.items():
        groups = sorted({q.get("type", q.get("category", "unknown")) for q in rows})
        output[split] = dict(query_count=len(rows), summary=summarize(rows),
                            categories=dict(Counter(q.get("type", q.get("category")) for q in rows)),
                            by_category={group: summarize([q for q in rows if q.get("type", q.get("category")) == group]) for group in groups},
                            ood_diagnostics=[ood_metrics(rows, 0.5), ood_metrics(rows, chosen["threshold"])], queries=rows)
    return dict(index=index, reproducibility=statistics, chunk_sensitivity=sensitivity,
                interpretation="Exposed-query regression after a splitter change; not a new independent holdout. Historical reports remain frozen.",
                threshold_calibration=dict(split="development", adopted=False, grid="0..1 step 0.05",
                                           criterion="Minimise FAR with at most one positive rejection; ties lower FRR then lower threshold",
                                           chosen=chosen), splits=output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, help="new JSON receipt directly inside evaluation/results")
    args = parser.parse_args(argv)
    if args.output:
        if args.output.resolve().parent != ROOT / "evaluation/results" or args.output.exists():
            parser.error("Output must be a new file directly inside evaluation/results")
    corpus = load_final_corpus()
    report = dict(schema_version=2, generated_at_utc=datetime.now(UTC).isoformat(),
                  corpus=dict(profile=corpus.manifest["profile"], documents=15, chunks=len(corpus.chunks),
                              chunk_sha256=corpus.manifest["chunks"]["sha256"]),
                  frozen_evidence=verify_history())
    if args.live:
        report["live"] = live_benchmark(corpus)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps(dict(status="PASS", corpus=report["corpus"], history="PASS",
                          live_summaries={key: value["summary"] for key, value in report.get("live", {}).get("splits", {}).items()}), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
