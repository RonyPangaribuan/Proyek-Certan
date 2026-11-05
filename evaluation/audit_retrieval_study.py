"""Independent-process verification of old baseline and reviewed-v2 evidence.

Read-only for source, chunks, indexes, frozen protocol, labels and results.
Writes a new verification report only. Never reruns label selection.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np

from audit_milestone3 import run as audit_baseline
from benchmark_semantic_retrieval import run as rerun_baseline
from build_reviewed_corpus import check_store, write_json
from retrieval_study import analyse, metrics, read, rule_path, sha

from proyek_certan.corpus.ingestion import load_corpus
from proyek_certan.corpus.revision import VERSION, revise_text
from proyek_certan.corpus.token_experiment import make_profile, token_length
from proyek_certan.knowledge.embeddings import EmbeddingModel, _load_model
from proyek_certan.knowledge.models import validate_chunks
from proyek_certan.knowledge.vector_store import VectorStore

ROOT = Path(__file__).resolve().parents[1]


def require(value, reason):
    if not value:
        raise ValueError(reason)


def run():
    protocol = read("evaluation/retrieval_study_protocol_v2.json")
    for path, expected in protocol["frozen_baseline_sha256"].items():
        require(sha(ROOT / path) == expected, f"baseline changed: {path}")
    baseline_integrity = audit_baseline()
    old = read("evaluation/semantic_retrieval_benchmark.json")
    rerun = rerun_baseline()  # run(), NOT its overwriting legacy __main__ block
    legacy_rank_variations = []
    for name, arm in old["profiles"].items():
        actual = rerun["profiles"][name]
        require(actual["summary"] == arm["summary"], f"{name}: legacy metrics changed")
        require(
            actual["threshold_analysis"] == arm["threshold_analysis"],
            f"{name}: legacy threshold behaviour changed",
        )
        for before, after in zip(arm["queries"], actual["queries"], strict=True):
            require(
                before["id"] == after["id"] and before["metrics"] == after["metrics"],
                f"{name}: legacy per-query metrics changed",
            )
            require(
                before["distinct_document_ranking"][:5] == after["distinct_document_ranking"][:5],
                f"{name}: legacy Top-5 document ranks changed",
            )
            if before["distinct_document_ranking"] != after["distinct_document_ranking"]:
                legacy_rank_variations.append({
                    "profile": name, "query_id": before["id"],
                    "frozen_ranking": before["distinct_document_ranking"],
                    "rerun_ranking": after["distinct_document_ranking"],
                })
    corpus = read("evaluation/reviewed_corpus_v2.json")
    require(
        corpus["provenance_corrections_sha256"] == sha(ROOT / "evaluation/source_provenance_v2.json"),
        "provenance corrections changed after build",
    )
    sources = read("evaluation/source_review_v2.json")
    require(
        sources["corpus_report_sha256"] == sha(ROOT / "evaluation/reviewed_corpus_v2.json"),
        "source audit refers to another corpus report",
    )
    for source in sources["documents"]:
        current_source = source.get("current_source", {})
        canonical = current_source.get("canonical_provenance")
        if canonical:
            require(canonical["pdf_bytes_equal_original"], "canonical PDF differs from original")
            require(canonical["extraction_equals_original"], "canonical PDF text differs")
            require(
                canonical["verified_source_url"] == source["verified_source_url"],
                "verified metadata URL differs from official canonical source",
            )
    loaded, audits = load_corpus(ROOT)
    docs = {d["document_id"]: d for d in corpus["documents"]}
    for item, audit in zip(loaded, audits, strict=True):
        d = docs[item["manifest"]["document_id"]]
        original = (ROOT / d["text_file"]).read_text(encoding="utf-8")
        corrected, operations = revise_text(d["document_id"], original)
        require(
            sha(ROOT / d["revised_text_file"]) == d["text_sha256"],
            "revised text hash mismatch",
        )
        require(
            (ROOT / d["revised_text_file"]).read_text(encoding="utf-8") == corrected,
            "revised text differs from deterministic correction",
        )
        require(
            d["operations"] == operations["operations"],
            "revision operation count differs",
        )
        item["text"] = corrected
        audit["review_required"] = d["review_required"]
    embedder = EmbeddingModel()
    model = _load_model(embedder.model_name, embedder.cache_folder)
    count = lambda text: token_length(model.tokenizer, text)
    indexes = {}
    for name, p in corpus["profiles"].items():
        require(
            sha(ROOT / p["chunk_file"]) == p["chunk_file_sha256"], "chunk hash mismatch"
        )
        actual = validate_chunks(
            json.loads((ROOT / p["chunk_file"]).read_text(encoding="utf-8"))
        )
        expected = make_profile(
            loaded, audits, count, p["max_total_tokens"], p["overlap_words_requested"]
        )
        require(len(actual) == len(expected), "deterministic chunk count differs")
        for a, e in zip(actual, expected, strict=True):
            require(
                a.text == e.text and a.chunk_id == f"{VERSION}-{e.chunk_id}",
                "deterministic chunk text/ID differs",
            )
            d = docs[a.metadata["document_id"]]
            for key, value in e.metadata.items():
                if key == "source_url":
                    value = d["verified_source_url"]
                require(a.metadata[key] == value, f"chunk metadata mismatch: {key}")
            if d["verified_source_url"] != d["source_url"]:
                require(a.metadata["historical_source_url"] == d["source_url"], "historical URL lost")
                require(a.metadata["source_revision"] == d["source_revision"], "source revision lost")
            for key in (
                "source_pdf_sha256",
                "text_sha256",
                "document_kind",
                "publisher",
                "extraction_method",
            ):
                require(a.metadata[key] == d[key], f"source metadata mismatch: {key}")
            require(a.metadata["corpus_version"] == VERSION, "corpus version lost")
            require(count(a.text) <= p["max_total_tokens"], "token cap exceeded")
        with VectorStore(ROOT / p["database_path"]) as store:
            check_store(store, actual)
            vectors = np.asarray(store.collection.get(include=["embeddings"])["embeddings"])
            require(vectors.shape == (len(actual), 384), "stored embedding shape differs")
            require(np.isfinite(vectors).all(), "non-finite stored embeddings")
            require(
                np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5),
                "stored embeddings are not unit-normalized",
            )
            indexes[name] = {
                "chunk_count": store.count(),
                "database_path": p["database_path"],
                "configuration": store.collection.configuration_json,
                "collection_metadata": store.collection.metadata,
                "telemetry_enabled": store.client.get_settings().anonymized_telemetry,
                "independent_process_persistence_verified": True,
                "stored_embedding_dimension": 384,
                "stored_embeddings_finite_and_normalized": True,
            }
            initial_path = ROOT / f".local/chroma-corpus-m3-{name}"
            if (initial_path / "chroma.sqlite3").exists():
                current = store.collection.get(include=["documents", "embeddings"])
                with VectorStore(initial_path) as initial:
                    prior_vectors = initial.collection.get(include=["documents", "embeddings"])
                current_map = dict(zip(current["ids"], zip(current["documents"], current["embeddings"]), strict=True))
                initial_map = dict(zip(prior_vectors["ids"], zip(prior_vectors["documents"], prior_vectors["embeddings"]), strict=True))
                require(set(current_map) == set(initial_map), "provenance correction changed chunk IDs")
                max_delta = 0.0
                for chunk_id, (text, vector) in current_map.items():
                    initial_text, initial_vector = initial_map[chunk_id]
                    require(text == initial_text, "provenance correction changed embedded text")
                    delta = float(np.max(np.abs(np.asarray(vector) - np.asarray(initial_vector))))
                    max_delta = max(max_delta, delta)
                require(max_delta <= 1e-6, "provenance correction changed embeddings")
                indexes[name]["provenance_reindex_check"] = {
                    "initial_database_path": initial_path.relative_to(ROOT).as_posix(),
                    "text_and_ids_identical": True,
                    "maximum_embedding_absolute_difference": max_delta,
                }
    labels = read("evaluation/retrieval_study_labels_v2.json")
    for doc_id, expected_hash in labels["source_text_sha256"].items():
        require(docs[doc_id]["original_text_sha256"] == expected_hash, "annotation source changed")
    require(
        sha(ROOT / "evaluation/retrieval_study_labels_v2.json")
        == protocol["labels_sha256"],
        "frozen labels changed",
    )
    for key in ("rules", "metadata_rule"):
        require(
            sha(rule_path(protocol["candidate"][f"{key}_file"]))
            == protocol["candidate"][f"{key}_sha256"],
            "candidate code changed after preregistration",
        )
    results = read("evaluation/retrieval_study_results_v2.json")
    require(
        results["protocol_sha256"]
        == sha(ROOT / "evaluation/retrieval_study_protocol_v2.json"),
        "protocol changed after retrieval",
    )
    require(
        results["corpus_report_sha256"]
        == sha(ROOT / "evaluation/reviewed_corpus_v2.json"),
        "corpus report changed after retrieval",
    )
    all_labels = {
        q["id"]: q
        for q in labels["queries"]
        + read("evaluation/semantic_retrieval_ground_truth.json")["queries"]
    }
    for name, arm in results["arms"].items():
        require(len(arm["queries"]) == 75, "incomplete query evaluation")
        for row in arm["queries"]:
            label = all_labels[row["id"]]
            require(
                row["query"] == label["query"]
                and row["relevant_documents"] == label["relevant_documents"],
                "ground truth differs across arms",
            )
            ranking = [d["document_id"] for d in row["documents"]]
            require(len(ranking) == len(set(ranking)), "duplicate document ranks")
            require(
                row["metrics"] == metrics(ranking, set(row["relevant_documents"])),
                "saved metrics arithmetic mismatch",
            )
        recalculated = analyse(arm["queries"], protocol["threshold_grid"])
        for key in recalculated:
            require(
                recalculated[key] == arm[key],
                f"{name}: development calibration or held-out summary mismatch",
            )
    cache = (
        Path(embedder.cache_folder)
        / "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
    )
    commit = (cache / "refs/main").read_text(encoding="utf-8").strip()
    snapshot = cache / "snapshots" / commit
    artifact_names = [
        "model.safetensors",
        "config.json",
        "sentence_bert_config.json",
        "modules.json",
        "tokenizer.json",
        "1_Pooling/config.json",
    ]
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "baseline_integrity": baseline_integrity,
        "legacy_benchmark_rerun_summaries_per_query_metrics_and_top5_identical": True,
        "legacy_document_rank_variations_beyond_top5": legacy_rank_variations,
        "legacy_output_not_rewritten": True,
        "frozen_labels_and_protocol_verified": True,
        "all_saved_metric_arithmetic_verified": True,
        "source_revisions_and_word_coverage_verified": True,
        "source_audit_sha256": sha(ROOT / "evaluation/source_review_v2.json"),
        "indexes": indexes,
        "model": {
            "name": embedder.model_name,
            "cached_hub_commit": commit,
            "dimension": embedder.dimension,
            "max_sequence_length": model.max_seq_length,
            "special_tokens": model.tokenizer.num_special_tokens_to_add(pair=False),
            "artifact_sha256": {name: sha(snapshot / name) for name in artifact_names},
        },
        "package_versions": {
            name: version(name)
            for name in [
                "sentence-transformers",
                "transformers",
                "torch",
                "chromadb",
                "numpy",
                "pypdf",
                "pytest",
            ]
        },
        "candidate_adopted": results["candidate_decision"]["adopt"],
    }
    write_json(ROOT / "evaluation/retrieval_study_verification_v2.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    run()
