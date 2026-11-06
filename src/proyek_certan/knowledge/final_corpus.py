"""Single active corpus configuration and integrity checks; no retrieval changes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from proyek_certan.knowledge.embeddings import DEFAULT_MODEL_NAME
from proyek_certan.knowledge.models import KnowledgeChunk, validate_chunks
from proyek_certan.knowledge.vector_store import COLLECTION_NAME, VectorStore


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = Path("data/corpus/final/manifest.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_path(root: Path, relative: str) -> Path:
    """Resolve portable manifest paths without permitting traversal or symlinks out."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Manifest path must be repository-relative: {relative}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Manifest path escapes repository: {relative}")
    return resolved


def checked_file(root: Path, relative: str, expected: str) -> Path:
    path = repository_path(root, relative)
    if sha256(path) != expected:
        raise ValueError(f"SHA-256 mismatch: {relative}")
    return path


@dataclass(frozen=True)
class FinalCorpus:
    root: Path
    manifest: dict
    chunks: list[KnowledgeChunk]

    @property
    def database_path(self) -> Path:
        return repository_path(self.root, self.manifest["storage"]["database_path"])

    @property
    def model_cache(self) -> Path:
        return repository_path(self.root, self.manifest["storage"]["model_cache"])


def load_final_corpus(root: Path | None = None) -> FinalCorpus:
    """Verify final bytes against the audited v3 source before using any database."""
    root = (root if root is not None else REPOSITORY_ROOT).resolve()
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    if (
        manifest["schema_version"] != 1
        or manifest["status"] != "ACTIVE"
        or manifest["corpus_version"] != "m3-reviewed-v3"
        or manifest["profile"] != "v3_t96_w10"
        or manifest["document_count"] != 15
        or manifest["chunk_count"] != 487
    ):
        raise ValueError("Only the audited v3_t96_w10 final corpus is active")
    if manifest["embedding"] != {
        "model_name": DEFAULT_MODEL_NAME,
        "dimension": 384,
        "normalize_embeddings": True,
    }:
        raise ValueError("Final embedding configuration differs from the audited model")
    if (
        manifest["chunking"]["max_total_tokens"] != 96
        or manifest["chunking"]["overlap_words_requested"] != 10
        or manifest["chunking"]["model_max_tokens"] != 128
        or manifest["storage"]["collection"] != COLLECTION_NAME
        or manifest["storage"]["distance"] != "cosine"
        or manifest["retrieval"]["relevance_threshold"] is not None
        or manifest["retrieval"]["guard_adopted"]
        or manifest["retrieval"]["title_reranking_adopted"]
    ):
        raise ValueError(
            "Final configuration differs from the adopted semantic pipeline"
        )
    provenance = manifest["provenance_report"]
    report = json.loads(
        checked_file(root, provenance["path"], provenance["sha256"]).read_text(
            encoding="utf-8"
        )
    )
    source_documents = {d["document_id"]: d for d in report["documents"]}
    documents = manifest["documents"]
    expected_ids = {f"DOC{n:02d}" for n in range(1, 16)}
    if len(documents) != 15 or {d["document_id"] for d in documents} != expected_ids:
        raise ValueError("Final corpus must contain exactly 15 unique document IDs")
    active_paths = set()
    for document in documents:
        original = source_documents[document["document_id"]]
        if document["provenance"] != original:
            raise ValueError("Source provenance was changed")
        if (
            document["text_sha256"] != original["text_sha256"]
            or document["origin_text_file"] != original["revised_text_file"]
            or document["source_pdf_sha256"] != original["source_pdf_sha256"]
            or document["source_pdf"] != f"data/corpus/raw/{original['filename']}"
        ):
            raise ValueError("Final source mapping differs from the audited provenance")
        active = checked_file(
            root, document["active_text_file"], document["text_sha256"]
        )
        if active.parent != (root / MANIFEST_PATH).parent:
            raise ValueError("Active text must be inside data/corpus/final")
        active_paths.add(active)
        checked_file(root, document["origin_text_file"], document["text_sha256"])
        checked_file(root, document["source_pdf"], document["source_pdf_sha256"])
    if active_paths != set((root / MANIFEST_PATH).parent.glob("*.txt")):
        raise ValueError("Unregistered or duplicate active text file")
    chunk_file = manifest["chunks"]
    profile = report["profiles"][manifest["profile"]]
    if (
        chunk_file["path"] != "data/corpus/final/knowledge_chunks.json"
        or chunk_file["origin_path"] != profile["chunk_file"]
        or chunk_file["sha256"] != profile["chunk_file_sha256"]
        or chunk_file["origin_sha256"] != chunk_file["sha256"]
    ):
        raise ValueError(
            "Final chunks must be an exact copy of the selected v3 profile"
        )
    checked_file(root, chunk_file["origin_path"], chunk_file["sha256"])
    chunks = validate_chunks(
        json.loads(
            checked_file(root, chunk_file["path"], chunk_file["sha256"]).read_text(
                encoding="utf-8"
            )
        )
    )
    if (
        len(chunks) != 487
        or {c.metadata["document_id"] for c in chunks} != expected_ids
    ):
        raise ValueError("Final chunks have an unexpected count or document coverage")
    for chunk in chunks:
        metadata = chunk.metadata
        original = source_documents[metadata["document_id"]]
        for key in (
            "title",
            "publisher",
            "document_kind",
            "source_url",
            "source_pdf_sha256",
            "text_sha256",
            "corpus_version",
            "extraction_method",
            "review_required",
        ):
            expected_value = (
                original.get("verified_source_url") or original.get(key)
                if key == "source_url"
                else original.get(key)
            )
            if metadata.get(key) != expected_value:
                raise ValueError(f"Chunk provenance mismatch: {chunk.chunk_id}/{key}")
        for key in ("license_url", "publication_status", "source_revision"):
            if original.get(key) is not None and metadata.get(key) != original[key]:
                raise ValueError(
                    f"Chunk source rights/status changed: {chunk.chunk_id}"
                )
        if (
            metadata["text_file"] != original["revised_text_file"]
            or metadata["chunk_profile"] != manifest["profile"]
            or not metadata.get("section")
        ):
            raise ValueError(f"Chunk metadata incomplete: {chunk.chunk_id}")
    return FinalCorpus(root, manifest, chunks)


def verify_index(store: VectorStore, corpus: FinalCorpus) -> dict:
    """Reject mixed/stale indexes; check persisted IDs, content, metadata and vectors."""
    found = store.collection.get(include=["documents", "metadatas", "embeddings"])
    expected = {chunk.chunk_id: chunk for chunk in corpus.chunks}
    if set(found["ids"]) != set(expected) or store.count() != len(expected):
        raise ValueError(
            "Index differs from final corpus; use a fresh database directory"
        )
    for id_, text, metadata in zip(
        found["ids"], found["documents"], found["metadatas"], strict=True
    ):
        if text != expected[id_].text or metadata != expected[id_].metadata:
            raise ValueError(f"Persisted final index content mismatch: {id_}")
    vectors = np.asarray(found["embeddings"], dtype=np.float32)
    if (
        vectors.shape != (len(expected), corpus.manifest["embedding"]["dimension"])
        or not np.isfinite(vectors).all()
        or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
    ):
        raise ValueError("Persisted final vectors have invalid dimensions or norms")
    return {"chunks": len(expected), "documents": 15, "dimension": vectors.shape[1]}
