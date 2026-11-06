"""Index chunk mappings and retrieve knowledge with natural-language queries."""

from __future__ import annotations

from collections.abc import Sequence
import math

import numpy as np

from proyek_certan.knowledge.embeddings import Embedder, EmbeddingModel
from proyek_certan.knowledge.models import ChunkInput, SearchResult, validate_chunks
from proyek_certan.knowledge.vector_store import VectorStore
from proyek_certan.knowledge.documents import (
    CorpusCatalog,
    DocumentResult,
    distinct_documents,
)


class KnowledgeRetriever:
    """Use the same encoder for document indexing and semantic search."""

    def __init__(self, store: VectorStore, embedder: Embedder | None = None) -> None:
        self.store = store
        self.embedder = (
            embedder if embedder is not None else EmbeddingModel(store.model_name)
        )
        if self.embedder.model_name != store.model_name:
            raise ValueError("Query and document embedding models must match")
        self._catalog = None
        self._title_vectors = None

    def index_chunks(self, chunks: Sequence[ChunkInput]) -> int:
        """Accept chunking output directly; an empty batch is a no-op."""
        batch = validate_chunks(chunks)
        if not batch:
            return 0
        embeddings = self.embedder.encode([chunk.text for chunk in batch])
        indexed = self.store.upsert(batch, embeddings)
        self._catalog = self._title_vectors = None
        return indexed

    def catalog(self) -> CorpusCatalog:
        if self._catalog is None:
            self._catalog = CorpusCatalog(
                self.store.collection.get(include=["metadatas"])["metadatas"]
            )
        return self._catalog

    def title_scores(self, query: str) -> dict[str, float]:
        """Cosine to source titles, encoded once per source inventory."""
        catalog = self.catalog()
        if not catalog.documents:
            return {}
        if self._title_vectors is None:
            self._title_vectors = self.embedder.encode(
                [str(m.get("title") or m["source"]) for m in catalog.documents.values()]
            )
        scores = self._title_vectors @ self.embedder.encode(query)[0]
        return dict(
            zip(
                catalog.documents,
                (float(np.clip(s, -1, 1)) for s in scores),
                strict=True,
            )
        )

    def search_documents(
        self, query: str, *, top_k: int = 5, candidate_depth: int = 100
    ) -> list[DocumentResult]:
        if type(top_k) is not int or top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        if type(candidate_depth) is not int or candidate_depth < top_k:
            raise ValueError("candidate_depth must be an integer >= top_k")
        return distinct_documents(self.search(query, top_k=candidate_depth))[:top_k]

    def search(
        self,
        query: str,
        *,
        top_k: int = 3,
        relevance_threshold: float | None = None,
    ) -> list[SearchResult]:
        """Return ranked chunks with similarity = 1 - cosine distance.

        Empty collections return []. Empty queries raise ValueError. An optional
        threshold in [-1, 1] filters the top-k candidates, so fewer than k may
        remain. No threshold is presumed optimal or enabled by default.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if type(top_k) is not int or top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        if relevance_threshold is not None:
            if (
                isinstance(relevance_threshold, bool)
                or not isinstance(relevance_threshold, (float, int))
                or not math.isfinite(relevance_threshold)
                or not -1.0 <= relevance_threshold <= 1.0
            ):
                raise ValueError(
                    "relevance_threshold must be finite and between -1 and 1"
                )
        if self.store.count() == 0:
            return []

        found = self.store.query(self.embedder.encode(query.strip()), top_k=top_k)
        documents = found["documents"][0]
        metadatas = found["metadatas"][0]
        distances = found["distances"][0]
        results = []
        for chunk_id, text, metadata, distance in zip(
            found["ids"][0], documents, metadatas, distances, strict=True
        ):
            # Clamp only floating-point roundoff at cosine's theoretical limits.
            similarity = max(-1.0, min(1.0, 1.0 - float(distance)))
            if relevance_threshold is not None and similarity < relevance_threshold:
                continue
            metadata = dict(metadata or {})
            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    text=text or "",
                    source=str(metadata.get("source", "")),
                    metadata=metadata,
                    similarity=similarity,
                )
            )
        return results
