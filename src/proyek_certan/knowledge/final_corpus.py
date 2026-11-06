"""Validate the sole active corpus without reading historical copies or scripts."""

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
EXPECTED_IDS = {f"DOC{n:02d}" for n in range(1, 16)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_path(root: Path, relative: str) -> Path:
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


def load_manifest(root: Path) -> dict:
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    if (manifest["schema_version"] != 2 or manifest["status"] != "ACTIVE"
            or manifest["corpus_version"] != "m3-final-recursive"
            or manifest["profile"] != "recursive_t96_w10"
            or manifest["document_count"] != 15):
        raise ValueError("Unsupported final corpus configuration")
    if manifest["embedding"] != dict(model_name=DEFAULT_MODEL_NAME, dimension=384,
                                     normalize_embeddings=True):
        raise ValueError("Final embedding configuration differs from the adopted model")
    if (manifest["chunking"]["max_total_tokens"] != 96
            or manifest["chunking"]["overlap_words_requested"] != 10
            or manifest["chunking"]["model_max_tokens"] != 128
            or manifest["storage"]["collection"] != COLLECTION_NAME
            or manifest["storage"]["distance"] != "cosine"
            or manifest["retrieval"]["relevance_threshold"] is not None
            or manifest["retrieval"]["guard_adopted"]
            or manifest["retrieval"]["title_reranking_adopted"]):
        raise ValueError("Final configuration differs from the adopted semantic pipeline")
    documents = manifest["documents"]
    if len(documents) != 15 or {d["document_id"] for d in documents} != EXPECTED_IDS:
        raise ValueError("Final corpus must contain exactly 15 unique document IDs")
    active_paths = set()
    for document in documents:
        active = checked_file(root, document["active_text_file"], document["text_sha256"])
        if active.parent != (root / MANIFEST_PATH).parent:
            raise ValueError("Active text must be inside data/corpus/final")
        active_paths.add(active)
        pdf = checked_file(root, document["source_pdf"], document["source_pdf_sha256"])
        if pdf.parent != root / "data/corpus/raw":
            raise ValueError("Source PDF must be inside data/corpus/raw")
        provenance = document["provenance"]
        if (provenance["document_id"] != document["document_id"]
                or provenance["text_sha256"] != document["text_sha256"]
                or provenance["source_pdf_sha256"] != document["source_pdf_sha256"]):
            raise ValueError("Final source mapping differs from its provenance")
    if active_paths != set((root / MANIFEST_PATH).parent.glob("*.txt")):
        raise ValueError("Unregistered or duplicate active text file")
    return manifest


def load_final_corpus(root: Path | None = None) -> FinalCorpus:
    root = (root if root is not None else REPOSITORY_ROOT).resolve()
    manifest = load_manifest(root)
    chunk_file = manifest["chunks"]
    if chunk_file["path"] != "data/corpus/final/knowledge_chunks.json":
        raise ValueError("Final chunks must be inside data/corpus/final")
    chunks = validate_chunks(json.loads(
        checked_file(root, chunk_file["path"], chunk_file["sha256"]).read_text(encoding="utf-8")
    ))
    if (len(chunks) != manifest["chunk_count"]
            or {c.metadata.get("document_id") for c in chunks} != EXPECTED_IDS):
        raise ValueError("Final chunks have an unexpected count or document coverage")
    by_id = {d["document_id"]: d for d in manifest["documents"]}
    for chunk in chunks:
        metadata = chunk.metadata
        document = by_id[metadata["document_id"]]
        provenance = document["provenance"]
        expected = dict(document_id=document["document_id"], source=provenance["filename"],
                        text_file=document["active_text_file"], corpus_version=manifest["corpus_version"],
                        chunk_profile=manifest["profile"], text_sha256=document["text_sha256"],
                        source_pdf_sha256=document["source_pdf_sha256"])
        for key in ("title", "publisher", "document_kind", "extraction_method", "language", "review_required"):
            expected[key] = provenance[key]
        expected["source_url"] = provenance.get("verified_source_url") or provenance["source_url"]
        for key in ("license_url", "publication_status", "source_revision"):
            if provenance.get(key) is not None:
                expected[key] = provenance[key]
        if any(metadata.get(key) != value for key, value in expected.items()):
            raise ValueError(f"Chunk provenance mismatch: {chunk.chunk_id}")
        if not metadata.get("section") or type(metadata.get("chunk_index")) is not int:
            raise ValueError(f"Chunk metadata incomplete: {chunk.chunk_id}")
    return FinalCorpus(root, manifest, chunks)


def verify_index(store: VectorStore, corpus: FinalCorpus) -> dict:
    found = store.collection.get(include=["documents", "metadatas", "embeddings"])
    expected = {chunk.chunk_id: chunk for chunk in corpus.chunks}
    if set(found["ids"]) != set(expected) or store.count() != len(expected):
        raise ValueError("Index differs from final corpus; use a fresh database directory")
    for id_, text, metadata in zip(found["ids"], found["documents"], found["metadatas"], strict=True):
        if text != expected[id_].text or metadata != expected[id_].metadata:
            raise ValueError(f"Persisted final index content mismatch: {id_}")
    vectors = np.asarray(found["embeddings"], dtype=np.float32)
    if (vectors.shape != (len(expected), corpus.manifest["embedding"]["dimension"])
            or not np.isfinite(vectors).all()
            or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)):
        raise ValueError("Persisted final vectors have invalid dimensions or norms")
    return dict(chunks=len(expected), documents=len(EXPECTED_IDS), dimension=vectors.shape[1])
