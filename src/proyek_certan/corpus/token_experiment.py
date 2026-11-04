"""Reproducible, token-bounded corpus chunking and isolated Chroma experiments.

Run from the repository root with ``uv run --frozen --no-sync python -m
proyek_certan.corpus.token_experiment``. The existing chunk JSON and databases
are read only.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import median
from time import perf_counter

from proyek_certan.corpus.chunking import chunk_document, group_short_sections, split_sections, chunk_section
from proyek_certan.corpus.ingestion import load_corpus
from proyek_certan.knowledge.embeddings import DEFAULT_MODEL_NAME, EmbeddingModel, _load_model
from proyek_certan.knowledge.models import KnowledgeChunk, validate_chunks
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


PROFILES = (("t120_w12", 120, 12), ("t96_w10", 96, 10))


def token_length(tokenizer: object, text: str) -> int:
    """Count the actual input IDs, including model special tokens."""
    return len(tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"])


def verify_coverage(text: str, chunks: list[KnowledgeChunk], size: int, overlap: int, count, cap: int) -> None:
    """Verify each section's ordered source words are covered, allowing overlap."""
    offset = 0
    sections = group_short_sections(split_sections(text, ""), size)
    if [word for section in sections for word in section.text.split()] != text.split():
        raise ValueError("section splitting lost or reordered source words")
    for section in sections:
        section_words = section.text.split()
        parts = chunk_section(section, size, overlap, token_count=count, max_tokens=cap)
        covered = 0
        for part in parts:
            piece = part.split()
            matches = [start for start in range(max(0, covered - len(piece)), covered + 1)
                       if section_words[start:start + len(piece)] == piece and start + len(piece) > covered]
            if not matches:
                raise ValueError("chunk sequence has a missing or reordered source word")
            covered = max(matches) + len(piece)
        if covered != len(section_words):
            raise ValueError("final source words are not covered")
        if [chunk.text for chunk in chunks[offset:offset + len(parts)]] != parts:
            raise ValueError("chunk sequence differs from verified section")
        offset += len(parts)
    if offset != len(chunks):
        raise ValueError("unexpected chunks after the last section")


def make_profile(loaded: list[dict], audits: list[dict], count, cap: int, overlap: int) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for item, audit in zip(loaded, audits, strict=True):
        doc = item["manifest"]
        produced = chunk_document(
            item["text"], document_id=doc["document_id"], source=doc["filename"],
            title=doc["title"], source_url=doc["source_url"], size=250,
            overlap=overlap, token_count=count, max_tokens=cap,
            review_required=audit["review_required"],
            publication_status=doc.get("publication_status"),
        )
        verify_coverage(item["text"], produced, 250, overlap, count, cap)
        chunks.extend(produced)
    validate_chunks(chunks)
    if any(count(chunk.text) > cap for chunk in chunks):
        raise ValueError("token limit violated")
    return chunks


def distribution(lengths: list[int]) -> dict[str, int]:
    edges = (("1-32", 1, 32), ("33-64", 33, 64), ("65-96", 65, 96),
             ("97-112", 97, 112), ("113-120", 113, 120), ("121-128", 121, 128))
    return {name: sum(low <= value <= high for value in lengths) for name, low, high in edges}


def run(root: Path) -> dict:
    root = root.resolve()
    baseline = json.loads((root / "evaluation/real_corpus_search.json").read_text(encoding="utf-8"))
    embedder = EmbeddingModel()
    model = _load_model(embedder.model_name, embedder.cache_folder)
    tokenizer = model[0].tokenizer
    max_sequence = int(model.max_seq_length)
    special_count = tokenizer.num_special_tokens_to_add(pair=False)
    if tokenizer.model_max_length != max_sequence or max_sequence != 128 or special_count != 2:
        raise ValueError("model/tokenizer limits changed; review experiment profiles")
    loaded, audits = load_corpus(root)
    doc_ids = {item["manifest"]["document_id"] for item in loaded}
    count = lambda text: token_length(tokenizer, text)
    baseline_path = root / baseline["database_path"]
    with VectorStore(baseline_path) as store:
        baseline_count_before = store.count()
    if baseline_count_before != baseline["stored_count"]:
        raise ValueError("baseline database count differs from previous report")
    baseline_chunks_sha = hashlib.sha256((root / "data/corpus/processed/knowledge_chunks.json").read_bytes()).hexdigest()
    if baseline_chunks_sha != baseline["input_sha256"]:
        raise ValueError("baseline chunk file differs from previous report")

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "experimental_not_production_approved",
        "model_name": DEFAULT_MODEL_NAME,
        "model_max_sequence_tokens": max_sequence,
        "tokenizer_max_length": tokenizer.model_max_length,
        "special_tokens_per_single_input": special_count,
        "maximum_content_tokens": max_sequence - special_count,
        "embedding_dimension": embedder.dimension,
        "baseline": {"chunks": baseline["input_chunk_count"],
                     "over_limit": baseline["token_lengths"]["over_limit_count"],
                     "database_path": baseline["database_path"],
                     "stored_count_before": baseline_count_before},
        "profiles": {},
    }
    for name, cap, overlap in PROFILES:
        chunks = make_profile(loaded, audits, count, cap, overlap)
        lengths = [count(chunk.text) for chunk in chunks]
        words = [len(chunk.text.split()) for chunk in chunks]
        counts = Counter(chunk.metadata["document_id"] for chunk in chunks)
        if set(counts) != doc_ids:
            raise ValueError(f"{name}: incomplete document coverage")
        output = root / f"data/corpus/processed/knowledge_chunks_{name}.json"
        output.write_text(json.dumps([asdict(chunk) for chunk in chunks], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        database = root / f".local/chroma-corpus-m3-{name}"
        if database.exists():
            raise FileExistsError(f"experiment database already exists: {database}")
        with VectorStore(database) as store:
            retriever = KnowledgeRetriever(store, embedder)
            started = perf_counter()
            indexed = retriever.index_chunks(chunks)
            elapsed = round(perf_counter() - started, 3)
            if indexed != len(chunks) or store.count() != len(chunks):
                raise ValueError(f"{name}: indexing count mismatch")
            stored = store.collection.get(include=["documents", "metadatas"])
            actual = {chunk_id: (text, metadata) for chunk_id, text, metadata in zip(
                stored["ids"], stored["documents"], stored["metadatas"], strict=True)}
            if any(actual.get(chunk.chunk_id) != (chunk.text, chunk.metadata) for chunk in chunks):
                raise ValueError(f"{name}: stored text or metadata differs")
            queries = {}
            for key, old in baseline["queries"].items():
                results = retriever.search(old["query"], top_k=old["top_k"])
                queries[key] = {"query": old["query"], "top_k": old["top_k"],
                                "results": [asdict(result) for result in results]}
        # Reopen the persistent collection in a separate process during validation below.
        profile = {
            "profile": name, "max_total_tokens": cap, "max_content_tokens": cap - special_count,
            "word_ceiling": 250, "overlap_words_requested": overlap,
            "boundary_priority": "section, then paragraph/line, then word",
            "overlap_scope": "within section; reduced only when needed for progress",
            "chunk_count": len(chunks), "document_count": len(counts),
            "chunks_per_document": dict(sorted(counts.items())),
            "token_lengths": {"min": min(lengths), "median": median(lengths),
                              "max": max(lengths), "mean": round(sum(lengths) / len(lengths), 2),
                              "distribution": distribution(lengths),
                              "over_model_limit": sum(length > max_sequence for length in lengths)},
            "word_lengths": {"min": min(words), "median": median(words), "max": max(words)},
            "source_word_coverage_verified": True,
            "unique_ids_verified": True, "stored_ids_text_metadata_verified": True,
            "database_path": str(database.relative_to(root)).replace("\\", "/"),
            "chunk_file": str(output.relative_to(root)).replace("\\", "/"),
            "chunk_file_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "index_duration_seconds": elapsed, "stored_count": indexed,
            "review_required_documents": [audit["document_id"] for audit in audits if audit["review_required"]],
        }
        summary["profiles"][name] = profile
        search_report = {"profile": name, "model_name": DEFAULT_MODEL_NAME,
                         "database_path": profile["database_path"], "stored_count": indexed,
                         "queries": queries}
        (root / f"evaluation/real_corpus_search_{name}.json").write_text(
            json.dumps(search_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with VectorStore(baseline_path) as store:
        summary["baseline"]["stored_count_after"] = store.count()
    if summary["baseline"]["stored_count_after"] != baseline_count_before:
        raise ValueError("baseline collection count changed")
    (root / "evaluation/token_chunking_comparison.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = run(Path.cwd())
    print(json.dumps({name: {"chunks": item["chunk_count"], "tokens": item["token_lengths"],
                             "seconds": item["index_duration_seconds"]}
                      for name, item in result["profiles"].items()}, ensure_ascii=False))
