"""Offline ingestion of reviewed source texts and recursive token-bounded chunks."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from statistics import median

from proyek_certan.corpus.chunking import chunk_document, chunk_section, group_short_sections, split_sections
from proyek_certan.corpus.cleaning import normalize_text
from proyek_certan.corpus.prepare import exact_page_span, pdf_word_pages
from proyek_certan.knowledge.final_corpus import load_manifest
from proyek_certan.knowledge.models import KnowledgeChunk, validate_chunks


def token_length(tokenizer, text: str) -> int:
    return len(tokenizer(text, add_special_tokens=True, truncation=False, verbose=False)["input_ids"])


def verify_coverage(text, chunks, size, overlap, count, cap):
    """Verify ordered source-word coverage, including overlaps and short sections."""
    offset = 0
    sections = group_short_sections(split_sections(text, ""), size)
    if [word for section in sections for word in section.text.split()] != text.split():
        raise ValueError("Section splitting lost or reordered source words")
    for section in sections:
        words = section.text.split()
        parts = chunk_section(section, size, overlap, token_count=count, max_tokens=cap)
        covered = 0
        for part in parts:
            piece = part.split()
            matches = [start for start in range(max(0, covered - len(piece)), covered + 1)
                       if words[start:start + len(piece)] == piece and start + len(piece) > covered]
            if not matches:
                raise ValueError("Chunk sequence has a missing or reordered source word")
            covered = max(matches) + len(piece)
        if covered != len(words) or [c.text for c in chunks[offset:offset + len(parts)]] != parts:
            raise ValueError("Source coverage differs from chunk sequence")
        offset += len(parts)
    if offset != len(chunks):
        raise ValueError("Unexpected chunks after last section")


def build_chunks(root: Path, tokenizer, *, cap: int = 96, overlap: int = 10):
    """Build in memory from verified TXT snapshots; never download or rewrite TXT.

    Thirteen reviewed texts came from official HTML; image-only source PDFs
    cannot regenerate those snapshots. Native-PDF sources retain their PDFs too.
    """
    root = root.resolve()
    manifest = load_manifest(root)
    count = lambda text: token_length(tokenizer, text)
    chunks: list[KnowledgeChunk] = []
    for document in manifest["documents"]:
        source = document["provenance"]
        text = normalize_text((root / document["active_text_file"]).read_text(encoding="utf-8"))
        produced = chunk_document(
            text, document_id=document["document_id"], source=source["filename"],
            title=source["title"], source_url=source.get("verified_source_url") or source["source_url"],
            size=250, overlap=overlap, token_count=count, max_tokens=cap,
            review_required=source["review_required"], publication_status=source.get("publication_status"),
        )
        verify_coverage(text, produced, 250, overlap, count, cap)
        page_index = pdf_word_pages(root / document["source_pdf"], document["document_id"]) if source["extraction_method"] == "pypdf" else None
        for chunk in produced:
            metadata = dict(chunk.metadata, text_file=document["active_text_file"],
                            text_sha256=document["text_sha256"], source_pdf_sha256=document["source_pdf_sha256"],
                            corpus_version=manifest["corpus_version"], chunk_profile=f"recursive_t{cap}_w{overlap}")
            for key in ("publisher", "document_kind", "language", "extraction_method", "license_url", "source_revision"):
                if source.get(key) is not None:
                    metadata[key] = source[key]
            metadata["review_note"] = source.get("unresolved") or "Reviewed text; topical relevance does not confer local policy authority."
            if page_index is not None:
                metadata.update(exact_page_span(chunk.text, source["title"], page_index))
            chunks.append(KnowledgeChunk(chunk.chunk_id, chunk.text, metadata))
    validate_chunks(chunks)
    lengths = [count(c.text) for c in chunks]
    if not lengths or max(lengths) > cap:
        raise ValueError("Token budget exceeded")
    return chunks, dict(document_count=15, chunk_count=len(chunks),
                        token_lengths=dict(min=min(lengths), median=median(lengths), max=max(lengths),
                                           over_model_limit=sum(n > 128 for n in lengths)),
                        source_word_coverage_verified=True)


def chunk_bytes(chunks) -> bytes:
    return (json.dumps([asdict(c) for c in chunks], ensure_ascii=False, indent=2) + "\n").encode("utf-8")
