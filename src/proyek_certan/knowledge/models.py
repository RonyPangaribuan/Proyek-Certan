"""Chunk integration contract, independent of ingestion and chunking."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import TypeAlias


MetadataValue: TypeAlias = str | int | float | bool
Metadata: TypeAlias = dict[str, MetadataValue]


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    """A stable chunk ID, text, and flat Chroma-compatible source metadata."""

    chunk_id: str
    text: str
    metadata: Metadata

    def __post_init__(self) -> None:
        for name in ("chunk_id", "text"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        for key, value in self.metadata.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("metadata keys must be non-empty strings")
            if type(value) not in (str, int, float, bool):
                raise TypeError("metadata values must be scalar str, int, float, or bool")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("metadata numbers must be finite")
        source = self.metadata.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("metadata.source must be a non-empty string")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> KnowledgeChunk:
        """Accept the chunk_id/text/metadata mapping supplied by another module."""
        try:
            return cls(
                chunk_id=value["chunk_id"],  # type: ignore[arg-type]
                text=value["text"],  # type: ignore[arg-type]
                metadata=value["metadata"],  # type: ignore[arg-type]
            )
        except KeyError as error:
            raise ValueError(f"Missing chunk field: {error.args[0]}") from error


ChunkInput: TypeAlias = KnowledgeChunk | Mapping[str, object]


def validate_chunks(chunks: Sequence[ChunkInput]) -> list[KnowledgeChunk]:
    """Validate a batch before encoding/writing; duplicate IDs in a batch fail."""
    result = []
    for chunk in chunks:
        if isinstance(chunk, KnowledgeChunk):
            # Revalidate potentially mutated metadata before writing.
            result.append(KnowledgeChunk(chunk.chunk_id, chunk.text, chunk.metadata))
        elif isinstance(chunk, Mapping):
            result.append(KnowledgeChunk.from_mapping(chunk))
        else:
            raise TypeError("each chunk must be a KnowledgeChunk or mapping")
    if len({chunk.chunk_id for chunk in result}) != len(result):
        raise ValueError("chunk_id values must be unique within a batch")
    return result


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A retrieved chunk with cosine similarity in [-1, 1], not a probability."""

    chunk_id: str
    text: str
    source: str
    metadata: Metadata
    similarity: float
