"""Persistent ChromaDB storage using explicit vectors and cosine distance."""

from __future__ import annotations

from collections.abc import Sequence
import os
from pathlib import Path

import chromadb
from chromadb.api.types import QueryResult
from chromadb.config import Settings
from chromadb.errors import ChromaError
import numpy as np
from numpy.typing import ArrayLike, NDArray

from proyek_certan.knowledge.embeddings import DEFAULT_MODEL_NAME
from proyek_certan.knowledge.models import ChunkInput, validate_chunks


COLLECTION_NAME = "certan_knowledge"


class VectorStoreError(RuntimeError):
    """A storage operation failed; the underlying exception is retained."""


def _matrix(embeddings: ArrayLike, rows: int) -> NDArray[np.float32]:
    matrix = np.asarray(embeddings, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] != rows or matrix.shape[1] == 0:
        raise ValueError("embeddings must have shape (number of chunks, dimension > 0)")
    if not np.isfinite(matrix).all() or np.any(np.linalg.norm(matrix, axis=1) == 0):
        raise ValueError("embeddings must contain finite, non-zero vectors")
    return matrix


class VectorStore:
    """Own a persistent client and a model-specific certan_knowledge collection.

    Paths default to CERTAN_CHROMA_PATH or .local/chroma relative to the working
    directory. Reopen using the same path; writes persist automatically.
    """

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        self.path = Path(
            path if path is not None else os.environ.get("CERTAN_CHROMA_PATH", ".local/chroma")
        ).expanduser().resolve()
        self.model_name = model_name
        self._closed = False
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.path), settings=Settings(anonymized_telemetry=False)
            )
            try:
                self.collection = self.client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    configuration={"hnsw": {"space": "cosine"}},
                    metadata={"certan_embedding_model": model_name},
                    embedding_function=None,
                )
                configuration = self.collection.configuration_json
                if (configuration.get("hnsw") or {}).get("space") != "cosine":
                    raise ValueError("Existing collection must use cosine distance")
                if (self.collection.metadata or {}).get("certan_embedding_model") != model_name:
                    raise ValueError(
                        "Existing collection uses a different or unknown embedding model; "
                        "use a separate database path and reindex with the desired model"
                    )
            except Exception:
                self.client.close()
                raise
        except (ChromaError, OSError) as error:
            raise VectorStoreError(f"Cannot open ChromaDB at {self.path}: {error}") from error

    def _ensure_open(self) -> None:
        if self._closed:
            raise VectorStoreError("Vector store is closed")

    def count(self) -> int:
        """Return the number of stored chunk IDs."""
        self._ensure_open()
        try:
            return self.collection.count()
        except ChromaError as error:
            raise VectorStoreError(f"Cannot count knowledge chunks: {error}") from error

    def upsert(self, chunks: Sequence[ChunkInput], embeddings: ArrayLike) -> int:
        """Insert or update aligned IDs, texts, metadata, and precomputed vectors.

        Existing IDs are updated without duplication. Large batches are split
        at Chroma's configured limit; writes across batches are not atomic.
        """
        self._ensure_open()
        batch = validate_chunks(chunks)
        if not batch:
            raise ValueError("chunks must not be empty")
        matrix = _matrix(embeddings, len(batch))
        batch_size = self.client.get_max_batch_size()
        try:
            for start in range(0, len(batch), batch_size):
                part = batch[start : start + batch_size]
                self.collection.upsert(
                    ids=[chunk.chunk_id for chunk in part],
                    documents=[chunk.text for chunk in part],
                    metadatas=[chunk.metadata for chunk in part],
                    embeddings=matrix[start : start + batch_size],
                )
        except (ChromaError, ValueError) as error:
            raise VectorStoreError(f"Cannot upsert knowledge chunks: {error}") from error
        return len(batch)

    def query(self, embedding: ArrayLike, *, top_k: int = 3) -> QueryResult:
        """Query one vector; cap top_k to the collection size."""
        self._ensure_open()
        if type(top_k) is not int or top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        matrix = _matrix(embedding, 1)
        count = self.count()
        if count == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        try:
            return self.collection.query(
                query_embeddings=matrix,
                n_results=min(top_k, count),
                include=["documents", "metadatas", "distances"],
            )
        except (ChromaError, ValueError) as error:
            raise VectorStoreError(f"Cannot query knowledge chunks: {error}") from error

    def close(self) -> None:
        """Release the client without deleting persisted data."""
        if not self._closed:
            self.client.close()
            self._closed = True

    def __enter__(self) -> VectorStore:
        self._ensure_open()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
