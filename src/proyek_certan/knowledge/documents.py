"""Distinct-document retrieval and source-derived evidence inventory.

No relevance labels, query IDs or preferred source IDs occur in this module.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from proyek_certan.knowledge.models import Metadata, SearchResult


@dataclass(frozen=True)
class DocumentResult:
    document_id: str
    chunk_id: str
    text: str
    source: str
    section: str
    similarity: float
    ranking_score: float
    metadata: Metadata
    ranking_reason: str
    candidate_chunk_count: int


def distinct_documents(results: Sequence[SearchResult]) -> list[DocumentResult]:
    """Use the maximum RAW chunk cosine once per document; stable on ties."""
    best: dict[str, SearchResult] = {}
    counts: dict[str, int] = {}
    for result in results:
        key = result.metadata.get("document_id")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("document-level retrieval requires metadata.document_id")
        counts[key] = counts.get(key, 0) + 1
        if key not in best or result.similarity > best[key].similarity:
            best[key] = result
    ranked = sorted(best.items(), key=lambda item: item[1].similarity, reverse=True)
    return [
        DocumentResult(
            doc,
            r.chunk_id,
            r.text,
            r.source,
            str(r.metadata.get("section", "")),
            r.similarity,
            r.similarity,
            dict(r.metadata),
            "Maximum cosine of retrieved chunks; one result per document.",
            counts[doc],
        )
        for doc, r in ranked
    ]
