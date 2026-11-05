"""Read-only integrity audit of the frozen Milestone 3 corpus and indexes.

Run from repository root with ``uv run --frozen --no-sync python
evaluation/audit_milestone3.py``. This script does not rewrite source artifacts.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from proyek_certan.corpus.ingestion import build_chunks, load_corpus
from proyek_certan.corpus.prepare import extract_pdf_text
from proyek_certan.corpus.token_experiment import make_profile, token_length
from proyek_certan.knowledge.embeddings import EmbeddingModel, _load_model
from proyek_certan.knowledge.models import validate_chunks
from proyek_certan.knowledge.vector_store import VectorStore


ROOT = Path(__file__).resolve().parents[1]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    loaded, audits = load_corpus(ROOT)  # validates TXT hashes and lengths
    manifest = json.loads((ROOT / "data/corpus/corpus_manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((ROOT / "evaluation/pdf_validation.json").read_text(encoding="utf-8"))
    comparisons = json.loads((ROOT / "evaluation/token_chunking_comparison.json").read_text(encoding="utf-8"))
    pdf_hashes = {item["filename"]: item["sha256"] for item in validation["documents"]}
    docs = manifest["documents"]
    check(len(docs) == len(loaded) == len(audits) == 15, "document count mismatch")
    check(len({doc["document_id"] for doc in docs}) == 15, "duplicate document ID")
    for doc in docs:
        check(sha(ROOT / "data/corpus/raw" / doc["filename"]) == pdf_hashes[doc["filename"]],
              f"{doc['document_id']}: raw PDF hash mismatch")
        if doc["document_id"] in {"DOC09", "DOC10"}:
            check(str(doc.get("publication_status", "")).startswith("DRAFT"),
                  f"{doc['document_id']}: DRAFT status missing")
        if doc["document_id"] in {"DOC11", "DOC13"}:
            check((ROOT / doc["text_file"]).read_text(encoding="utf-8") ==
                  extract_pdf_text(ROOT / "data/corpus/raw" / doc["filename"], doc["title"]),
                  f"{doc['document_id']}: TXT differs from local source PDF extraction")

    model = EmbeddingModel(comparisons["model_name"])
    tokenizer = _load_model(model.model_name, model.cache_folder).tokenizer
    count = lambda text: token_length(tokenizer, text)
    check(int(_load_model(model.model_name, model.cache_folder).max_seq_length) == 128,
          "model sequence length changed")
    check(tokenizer.num_special_tokens_to_add(pair=False) == 2, "special token count changed")
    expected_baseline, _ = build_chunks(ROOT)
    profiles = {"baseline": {"chunks": expected_baseline,
                              "chunk_file": "data/corpus/processed/knowledge_chunks.json",
                              "database_path": "evaluation/real_corpus_search.json"}}
    for name, cap, overlap in (("t120_w12", 120, 12), ("t96_w10", 96, 10)):
        profile = comparisons["profiles"][name]
        expected = make_profile(loaded, audits, count, cap, overlap)
        profiles[name] = {"chunks": expected, "chunk_file": profile["chunk_file"],
                          "database_path": profile["database_path"], "cap": cap}
    final_path = ROOT / ".local/chroma-corpus-m3-final"
    if final_path.exists():
        profiles["final_t96_w10"] = {**profiles["t96_w10"],
                                     "database_path": ".local/chroma-corpus-m3-final"}

    counts = {}
    baseline_report_hash_matches = None
    for name, profile in profiles.items():
        chunk_path = ROOT / profile["chunk_file"]
        actual = json.loads(chunk_path.read_text(encoding="utf-8"))
        validate_chunks(actual)
        expected = [asdict(chunk) for chunk in profile["chunks"]]
        check(actual == expected, f"{name}: chunk file differs from deterministic regeneration")
        if name != "baseline":
            comparison_name = "t96_w10" if name == "final_t96_w10" else name
            check(sha(chunk_path) == comparisons["profiles"][comparison_name]["chunk_file_sha256"],
                  f"{name}: chunk hash differs from comparison")
            lengths = [count(item["text"]) for item in actual]
            check(max(lengths) <= profile["cap"], f"{name}: token cap exceeded")
        else:
            baseline = json.loads((ROOT / profile["database_path"]).read_text(encoding="utf-8"))
            baseline_report_hash_matches = sha(chunk_path) == baseline["input_sha256"]
            check(baseline_report_hash_matches, "baseline report hash mismatch")
            profile["database_path"] = baseline["database_path"]
        grouped: dict[str, list[dict]] = defaultdict(list)
        for item in actual:
            grouped[item["metadata"]["document_id"]].append(item)
        check(set(grouped) == {doc["document_id"] for doc in docs}, f"{name}: missing document")
        for doc in docs:
            for item in grouped[doc["document_id"]]:
                metadata = item["metadata"]
                check(metadata["source"] == doc["filename"] and
                      metadata["title"] == doc["title"] and
                      metadata["source_url"] == doc["source_url"] and
                      bool(metadata["section"]) and
                      isinstance(metadata["chunk_index"], int),
                      f"{name}/{doc['document_id']}: incomplete metadata")
                if doc["document_id"] in {"DOC09", "DOC10"}:
                    check(metadata.get("publication_status") == doc["publication_status"],
                          f"{name}/{doc['document_id']}: DRAFT lost")
        with VectorStore(ROOT / profile["database_path"], model_name=model.model_name) as store:
            stored = store.collection.get(include=["documents", "metadatas"])
            indexed = {id_: (text, meta) for id_, text, meta in zip(
                stored["ids"], stored["documents"], stored["metadatas"], strict=True)}
            check(store.count() == len(actual) == len(indexed), f"{name}: index count mismatch")
            check(indexed == {item["chunk_id"]: (item["text"], item["metadata"]) for item in actual},
                  f"{name}: stored ID/text/metadata mismatch")
        counts[name] = {"chunks": len(actual), "documents": len(grouped),
                        "max_tokens_including_specials": max(lengths) if name != "baseline" else None,
                        "persistent_index_verified": True}
    return {"source_documents": len(docs), "raw_pdf_hashes_verified": True,
            "txt_hashes_verified": True, "local_pdf_extraction_verified": ["DOC11", "DOC13"],
            "deterministic_chunks_and_source_coverage_verified": True,
            "baseline_report_hash_matches": baseline_report_hash_matches,
            "profiles": counts,
            "review_required_documents": [audit["document_id"] for audit in audits if audit["review_required"]]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
