"""Index chunk mappings and retrieve knowledge with natural-language queries."""

from __future__ import annotations

from collections.abc import Sequence
import math

from proyek_certan.knowledge.embeddings import Embedder, EmbeddingModel
from proyek_certan.knowledge.models import ChunkInput, SearchResult, validate_chunks
from proyek_certan.knowledge.vector_store import VectorStore


class KnowledgeRetriever:
    """Use the same encoder for document indexing and semantic search."""

    def __init__(self, store: VectorStore, embedder: Embedder | None = None) -> None:
        self.store = store
        self.embedder = embedder if embedder is not None else EmbeddingModel(store.model_name)
        if self.embedder.model_name != store.model_name:
            raise ValueError("Query and document embedding models must match")

    def index_chunks(self, chunks: Sequence[ChunkInput]) -> int:
        """Accept chunking output directly; an empty batch is a no-op."""
        batch = validate_chunks(chunks)
        if not batch:
            return 0
        embeddings = self.embedder.encode([chunk.text for chunk in batch])
        return self.store.upsert(batch, embeddings)

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
                raise ValueError("relevance_threshold must be finite and between -1 and 1")
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
