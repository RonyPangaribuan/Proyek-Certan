"""Opt-in metadata reranking experiment. Never changes cosine similarity.

Rules and the fixed 0.10 ranking bonus are preregistered before retrieval.
No document IDs, ground-truth labels, or per-query exceptions are used.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from proyek_certan.knowledge.models import SearchResult


BONUS = 0.10


def query_intent(query: str) -> str | None:
    q = query.casefold()
    policy = bool(re.search(r"\b(aturan|kebijakan|diizinkan|izin|boleh|dilarang|wewenang|berwenang|persetujuan|larangan)\b", q))
    diagnostic = bool(re.search(r"\b(diagnosis|diagnosa|troubleshooting|memeriksa|cek|gagal|terputus|drop|pktmon|ping|error|galat)\b", q))
    # Mixed or unrecognised intent falls back to semantic order.
    if policy == diagnostic:
        return None
    return "network_policy" if policy else "diagnostic"


def rank_documents(results: Sequence[SearchResult], *, query: str | None = None) -> list[SearchResult]:
    """Best raw chunk per document, then optionally apply a metadata bonus.

    Distinct documents use maximum cosine. Deduplication is shared by the
    baseline and candidate; only metadata ranking differs. Python's stable sort
    preserves the original semantic order on ties. Candidate depth is fixed at
    100 chunks in the benchmark, so a missing candidate cannot be recovered.
    """
    best: dict[str, SearchResult] = {}
    for result in results:
        doc_id = str(result.metadata["document_id"])
        if doc_id not in best or result.similarity > best[doc_id].similarity:
            best[doc_id] = result
    intent = query_intent(query) if query is not None else None
    return sorted(best.values(), key=lambda result: result.similarity + (
        BONUS if intent is not None and result.metadata.get("document_kind") == intent else 0.0
    ), reverse=True)
