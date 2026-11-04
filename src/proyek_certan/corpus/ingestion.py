"""Audit manifest-listed UTF-8 texts and create index-ready knowledge chunks.

Run from the repository root:
`uv run --frozen --no-sync python -m proyek_certan.corpus.ingestion`
No PDF, embedding model, or Chroma database is modified.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
from statistics import median

from proyek_certan.corpus.chunking import chunk_document, heading_title, split_sections
from proyek_certan.corpus.cleaning import normalize_text
from proyek_certan.knowledge.models import KnowledgeChunk, validate_chunks


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def audit_text(document: dict, original: str, cleaned: str, sha256: str) -> dict:
    lines = cleaned.splitlines()
    heading_count = sum(bool(re.match(r"^#{1,6} ", line)) for line in lines)
    list_item_count = sum(bool(re.match(r"^\s*(?:[-*]|\d+[.)])\s+", line)) for line in lines)
    flags = []
    if not cleaned.strip():
        flags.append("empty_text")
    if not heading_count:
        flags.append("missing_markdown_heading")
    if "\ufffd" in original:
        flags.append("replacement_characters")
    if re.search(r"[\x00-\x08\x0b\x0e-\x1f]", original):
        flags.append("control_characters")
    if max((len(line) for line in lines), default=0) > 500:
        flags.append("long_source_lines")
    if document.get("source_status") == "processed_pdf":
        if len(lines) >= 80 and sum(20 <= len(line) <= 120 for line in lines) / len(lines) > 0.5:
            flags.append("pdf_hard_wrapped_lines")
        if re.search(r"(?m)^\s*\d{1,3}\s*$", cleaned) or re.search(r"\.{8,}", cleaned):
            flags.append("pdf_layout_artifacts")
    if any(line.count("$ ovs-vsctl") > 1 for line in lines):
        flags.append("multiple_commands_on_one_line")
    if str(document.get("publication_status", "")).startswith("DRAFT"):
        flags.append("draft_source")
    sections = split_sections(cleaned, document["title"])
    review_flags = {
        "replacement_characters", "control_characters", "pdf_layout_artifacts",
        "pdf_hard_wrapped_lines", "multiple_commands_on_one_line", "draft_source",
    }
    return {
        "document_id": document["document_id"],
        "text_file": document["text_file"],
        "sha256": sha256,
        "source_character_count": len(original),
        "cleaned_character_count": len(cleaned),
        "word_count": len(cleaned.split()),
        "markdown_heading_count": heading_count,
        "section_count": len(sections),
        "list_item_count": list_item_count,
        "question_count": sum(line.startswith("Q: ") for line in lines),
        "quality_flags": flags,
        "review_required": bool(review_flags.intersection(flags)),
    }


def load_corpus(root: Path) -> tuple[list[dict], list[dict]]:
    root = root.resolve()
    manifest = json.loads((root / "data/corpus/corpus_manifest.json").read_text(encoding="utf-8"))
    report = json.loads((root / "evaluation/corpus_processing.json").read_text(encoding="utf-8"))
    prior = {item["document_id"]: item for item in report["documents"]}
    documents = manifest["documents"]
    if len(prior) != len(documents):
        raise ValueError("manifest and processing report have different document counts")
    ids = [item["document_id"] for item in documents]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate document_id in manifest")
    processed_dir = (root / "data/corpus/processed").resolve()
    loaded = []
    audits = []
    for document in documents:
        doc_id = document["document_id"]
        previous = prior.get(doc_id)
        if not previous or previous["status"] != "processed":
            raise ValueError(f"{doc_id}: missing successful processing report")
        relative = document.get("text_file")
        if not isinstance(relative, str) or relative != previous["text_file"]:
            raise ValueError(f"{doc_id}: text_file differs from processing report")
        path = (root / relative).resolve()
        if not path.is_relative_to(processed_dir) or path.suffix.lower() != ".txt":
            raise ValueError(f"{doc_id}: text_file must be a TXT inside processed/")
        if path.name != Path(document["filename"]).stem + ".txt":
            raise ValueError(f"{doc_id}: text_file does not match source PDF")
        if _sha256(path) != previous["sha256"]:
            raise ValueError(f"{doc_id}: text SHA-256 differs from processing report")
        original = path.read_text(encoding="utf-8")
        if len(original) != previous["character_count"]:
            raise ValueError(f"{doc_id}: text length differs from processing report")
        cleaned = normalize_text(original)
        if not cleaned.strip():
            raise ValueError(f"{doc_id}: empty cleaned text")
        audits.append(audit_text(document, original, cleaned, previous["sha256"]))
        loaded.append({"manifest": document, "text": cleaned})
    return loaded, audits


def build_chunks(root: Path, size: int = 250, overlap: int = 40) -> tuple[list[KnowledgeChunk], dict]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("require size > 0 and 0 <= overlap < size")
    loaded, audits = load_corpus(root)
    chunks: list[KnowledgeChunk] = []
    for item, audit in zip(loaded, audits, strict=True):
        document = item["manifest"]
        produced = chunk_document(
            item["text"],
            document_id=document["document_id"],
            source=document["filename"],
            title=document["title"],
            source_url=document["source_url"],
            size=size,
            overlap=overlap,
            review_required=audit["review_required"],
            publication_status=document.get("publication_status"),
        )
        if not produced:
            raise ValueError(f"{document['document_id']}: no chunks produced")
        chunks.extend(produced)
    validate_chunks(chunks)
    lengths = [len(chunk.text.split()) for chunk in chunks]
    distribution = {
        "1-49": sum(length < 50 for length in lengths),
        "50-99": sum(50 <= length < 100 for length in lengths),
        "100-149": sum(100 <= length < 150 for length in lengths),
        "150-199": sum(150 <= length < 200 for length in lengths),
        "200-250": sum(200 <= length <= 250 for length in lengths),
    }
    counts = Counter(chunk.metadata["document_id"] for chunk in chunks)
    flags = Counter(flag for audit in audits for flag in audit["quality_flags"])
    report = {
        "method": {
            "size_words": size,
            "overlap_words": overlap,
            "word_definition": "non-whitespace token",
            "boundary_priority": "section, then line/paragraph, then word",
            "overlap_scope": "within each section; reset at section boundaries",
            "semantic_completeness": "not proven by automated audit; review source layout and technical content",
        },
        "summary": {
            "document_count": len(loaded),
            "chunk_count": len(chunks),
            "chunk_words_min": min(lengths),
            "chunk_words_median": median(lengths),
            "chunk_words_max": max(lengths),
            "chunk_words_mean": round(sum(lengths) / len(lengths), 2),
            "source_word_count": sum(audit["word_count"] for audit in audits),
            "chunk_length_distribution": distribution,
            "documents_with_quality_flags": sum(bool(audit["quality_flags"]) for audit in audits),
            "documents_requiring_content_review": sum(audit["review_required"] for audit in audits),
            "quality_flag_counts": dict(sorted(flags.items())),
        },
        "chunks_per_document": dict(sorted(counts.items())),
        "documents": audits,
    }
    return chunks, report


def write_outputs(root: Path, chunks: list[KnowledgeChunk], report: dict) -> None:
    output = root / "data/corpus/processed/knowledge_chunks.json"
    output.write_text(json.dumps([asdict(chunk) for chunk in chunks], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evaluation = root / "evaluation/corpus_chunking.json"
    evaluation.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--size", type=int, default=250)
    parser.add_argument("--overlap", type=int, default=40)
    args = parser.parse_args(argv)
    try:
        chunks, report = build_chunks(args.root, args.size, args.overlap)
        write_outputs(args.root, chunks, report)
    except (OSError, UnicodeError, KeyError, TypeError, ValueError) as exc:
        parser.exit(2, f"Corpus ingestion failed: {exc}\n")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
