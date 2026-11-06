"""Distinct-document retrieval and source-derived evidence inventory.

No relevance labels, query IDs or preferred source IDs occur in this module.
"""

from __future__ import annotations

import re
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


def normalized(text: str) -> str:
    return " ".join(re.findall(r"[\w]+", text.casefold()))


class CorpusCatalog:
    """Source inventory, not evidence that every requested answer is present."""

    def __init__(self, metadatas: Sequence[Metadata]):
        self.documents: dict[str, Metadata] = {}
        self.institutions: dict[str, str] = {}
        for metadata in metadatas:
            doc = metadata.get("document_id")
            if not isinstance(doc, str) or not doc.strip():
                raise ValueError("source inventory requires metadata.document_id")
            if doc in self.documents:
                for key in ("title", "publisher", "corpus_version"):
                    if self.documents[doc].get(key) != metadata.get(key):
                        raise ValueError(f"conflicting source metadata: {key}")
                continue
            self.documents[doc] = dict(metadata)
            publisher = str(metadata.get("publisher", ""))
            if not re.search(
                r"university|universitas|institute|institut|college", publisher, re.I
            ):
                continue
            full = normalized(publisher)
            tokens = full.split()
            # These are organizational boilerplate words, not query topic lists.
            stop = {"the", "of", "information", "technology", "dtsi"}
            name_tokens = [t for t in tokens if t not in stop]
            aliases = {full, " ".join(name_tokens), "".join(t[0] for t in name_tokens)}
            aliases.add(
                " ".join(
                    t
                    for t in name_tokens
                    if t not in {"university", "universitas", "college", "bloomington"}
                )
            )
            # Full institution name minus a trailing campus qualifier.
            if "bloomington" in name_tokens:
                aliases.add(" ".join(t for t in name_tokens if t != "bloomington"))
            for alias in aliases:
                if len(alias) >= 3:
                    self.institutions[alias] = publisher

    def matching_publishers(self, query: str) -> set[str]:
        q = f" {normalized(query)} "
        return {
            publisher
            for alias, publisher in self.institutions.items()
            if f" {alias} " in q
        }

    def supports_institution(self, name: str) -> bool:
        return bool(self.matching_publishers(name))
