"""Run the frozen document-level retrieval benchmark against both persistent indexes.

From repository root: uv run --frozen --no-sync python evaluation/benchmark_semantic_retrieval.py
The label file is hand-authored from the processed corpus and is never rewritten here.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from proyek_certan.knowledge.embeddings import EmbeddingModel
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


ROOT = Path(__file__).resolve().parents[1]
K_VALUES = (1, 3, 5)
RAW_DEPTH = 100
PROFILES = ("t120_w12", "t96_w10")
THRESHOLDS = (0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)


def metrics(ranked_documents: list[str], relevant: set[str]) -> dict:
    """Score distinct document ranks; no-reference queries have no recall or MRR."""
    result = {}
    for k in K_VALUES:
        hits = sum(doc in relevant for doc in ranked_documents[:k])
        result[f"recall@{k}"] = hits / len(relevant) if relevant else None
        result[f"precision@{k}"] = hits / k
    result["mrr"] = (
        next((1 / rank for rank, doc in enumerate(ranked_documents, 1) if doc in relevant), 0.0)
        if relevant else None
    )
    return result


def average(rows: list[dict], key: str) -> float | None:
    values = [row[key] for row in rows if row[key] is not None]
    return sum(values) / len(values) if values else None


def run() -> dict:
    labels_path = ROOT / "evaluation/semantic_retrieval_ground_truth.json"
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    comparison = json.loads((ROOT / "evaluation/token_chunking_comparison.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data/corpus/corpus_manifest.json").read_text(encoding="utf-8"))
    known = {doc["document_id"] for doc in manifest["documents"]}
    queries = labels["queries"]
    assert len(queries) >= 10 and len({q["id"] for q in queries}) == len(queries)
    assert {"relevant", "paraphrase", "ambiguous", "out_of_domain"} <= {q["type"] for q in queries}
    for query in queries:
        assert set(query["relevant_documents"]) <= known
        assert bool(query["relevant_documents"]) != (query["type"] == "out_of_domain")

    embedder = EmbeddingModel(comparison["model_name"])
    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ground_truth_file": "evaluation/semantic_retrieval_ground_truth.json",
        "ground_truth_sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest(),
        "model_name": comparison["model_name"],
        "unit": "distinct document_id (first occurrence among 100 raw chunks); MRR truncated at raw rank 100",
        "raw_depth": RAW_DEPTH,
        "k_values": list(K_VALUES),
        "thresholds": list(THRESHOLDS),
        "profiles": {},
    }
    for name in PROFILES:
        profile = comparison["profiles"][name]
        chunk_path = ROOT / profile["chunk_file"]
        assert hashlib.sha256(chunk_path.read_bytes()).hexdigest() == profile["chunk_file_sha256"]
        with VectorStore(ROOT / profile["database_path"], model_name=comparison["model_name"]) as store:
            assert store.count() == profile["chunk_count"]
            retriever = KnowledgeRetriever(store, embedder)
            rows = []
            for query in queries:
                found = retriever.search(query["query"], top_k=RAW_DEPTH)
                ranking = [
                    {"rank": rank, "chunk_id": item.chunk_id,
                     "document_id": item.metadata["document_id"],
                     "similarity": item.similarity,
                     "section": item.metadata.get("section", ""),
                     "review_required": item.metadata.get("review_required", False),
                     "publication_status": item.metadata.get("publication_status")}
                    for rank, item in enumerate(found, 1)
                ]
                distinct = []
                for item in ranking:
                    if item["document_id"] not in distinct:
                        distinct.append(item["document_id"])
                assert len(distinct) >= max(K_VALUES), f"{name}/{query['id']}: insufficient distinct documents"
                relevant = set(query["relevant_documents"])
                rows.append({"id": query["id"], "type": query["type"], "query": query["query"],
                             "relevant_documents": query["relevant_documents"],
                             "ranking": ranking, "distinct_document_ranking": distinct,
                             "metrics": metrics(distinct, relevant),
                             "top1_relevant": bool(distinct and distinct[0] in relevant)})
        positive = [row["metrics"] for row in rows if row["relevant_documents"]]
        summary = {key: average(positive, key) for key in
                   [f"{metric}@{k}" for metric in ("recall", "precision") for k in K_VALUES] + ["mrr"]}
        summary["positive_query_count"] = len(positive)
        summary["ood_query_count"] = len(rows) - len(positive)
        summary["top1_correct_count"] = sum(row["top1_relevant"] for row in rows if row["relevant_documents"])
        threshold_analysis = []
        for threshold in THRESHOLDS:
            accepted_positive = [row for row in rows if row["relevant_documents"] and row["ranking"][0]["similarity"] >= threshold]
            accepted_ood = [row for row in rows if not row["relevant_documents"] and row["ranking"][0]["similarity"] >= threshold]
            threshold_analysis.append({
                "threshold": threshold,
                "accepted_relevant_queries": len(accepted_positive),
                "accepted_relevant_with_correct_top1": sum(row["top1_relevant"] for row in accepted_positive),
                "accepted_ood_queries": [row["id"] for row in accepted_ood],
                "rejected_relevant_queries": [row["id"] for row in rows if row["relevant_documents"] and row not in accepted_positive],
            })
        output["profiles"][name] = {
            "chunk_count": profile["chunk_count"], "index_duration_seconds": profile["index_duration_seconds"],
            "database_path": profile["database_path"], "chunk_file_sha256": profile["chunk_file_sha256"],
            "queries": rows, "summary": summary, "threshold_analysis": threshold_analysis,
        }
    return output


if __name__ == "__main__":
    result = run()
    path = ROOT / "evaluation/semantic_retrieval_benchmark.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: data["summary"] for name, data in result["profiles"].items()}, indent=2))
