"""Reusable, normalized multilingual sentence embeddings."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
import os
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Embedder(Protocol):
    """Interface shared by indexing and query encoding."""

    model_name: str

    def encode(self, texts: str | Sequence[str]) -> NDArray[np.float32]:
        """Return a normalized matrix with one row per input text."""
        ...


@lru_cache(maxsize=2)
def _load_model(model_name: str, cache_folder: str) -> SentenceTransformer:
    """Load lazily and reuse a model across encoder instances in this process."""
    from sentence_transformers import SentenceTransformer

    try:
        return SentenceTransformer(model_name, cache_folder=cache_folder)
    except (OSError, RuntimeError, ValueError) as error:
        raise RuntimeError(
            f"Cannot load embedding model {model_name!r}. On first use, allow "
            "Hugging Face downloads; for offline use, populate the model cache first."
        ) from error


class EmbeddingModel:
    """Encode one or more texts without reloading the model on each call."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        *,
        cache_folder: str | Path | None = None,
    ) -> None:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        self.model_name = model_name
        cache = cache_folder if cache_folder is not None else os.environ.get(
            "CERTAN_MODEL_CACHE", ".cache/models"
        )
        self.cache_folder = str(Path(cache).expanduser().resolve())

    @property
    def dimension(self) -> int:
        """Return the loaded model's embedding dimension."""
        dimension = _load_model(
            self.model_name, self.cache_folder
        ).get_embedding_dimension()
        if dimension is None or dimension <= 0:
            raise RuntimeError("Embedding model has no valid output dimension")
        return int(dimension)

    def encode(self, texts: str | Sequence[str]) -> NDArray[np.float32]:
        """Return an (N, D) float32 matrix; reject empty texts and batches.

        A single string returns (1, D), preserving the batch axis. Whitespace
        is stripped before encoding. Validation happens before loading a model.
        """
        if isinstance(texts, str):
            batch = [texts]
        elif isinstance(texts, Sequence) and not isinstance(texts, bytes):
            batch = list(texts)
        else:
            raise TypeError("texts must be a string or a sequence of strings")
        if not batch:
            raise ValueError("texts must not be empty")
        if any(not isinstance(text, str) for text in batch):
            raise TypeError("each text must be a string")
        if any(not text.strip() for text in batch):
            raise ValueError("each text must not be empty or whitespace")

        model = _load_model(self.model_name, self.cache_folder)
        embeddings = np.asarray(
            model.encode(
                [text.strip() for text in batch],
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            ),
            dtype=np.float32,
        )
        if embeddings.shape != (len(batch), self.dimension):
            raise RuntimeError("Embedding model returned an unexpected matrix shape")
        if not np.isfinite(embeddings).all() or not np.allclose(
            np.linalg.norm(embeddings, axis=1), 1.0, atol=1e-5
        ):
            raise RuntimeError("Embedding model returned invalid or unnormalized vectors")
        return embeddings


def embed_texts(texts: str | Sequence[str]) -> NDArray[np.float32]:
    """Encode with the default cached multilingual model."""
    return EmbeddingModel().encode(texts)
