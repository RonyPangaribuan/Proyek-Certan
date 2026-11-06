"""Offline storage contract for the final corpus and a stub encoder."""

import json
from pathlib import Path
import subprocess
import sys

from proyek_certan.knowledge.models import validate_chunks
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


CORPUS_CHUNKS = (
    Path(__file__).resolve().parents[2] / "data/corpus/final/knowledge_chunks.json"
)


def test_real_chunks_index_reopen_and_retrieve_with_stub(tmp_path, embedder):
    chunks = json.loads(CORPUS_CHUNKS.read_text(encoding="utf-8"))
    validated = validate_chunks(chunks)
    expected_count = len(validated)
    assert expected_count > 0
    with VectorStore(tmp_path) as store:
        retriever = KnowledgeRetriever(store, embedder)
        assert retriever.index_chunks(chunks) == expected_count
        assert store.count() == expected_count
        stored = store.collection.get(include=["metadatas"])
        assert set(stored["ids"]) == {chunk.chunk_id for chunk in validated}
        assert {metadata["document_id"] for metadata in stored["metadatas"]} == {
            f"DOC{number:02d}" for number in range(1, 16)
        }
        assert all(
            metadata["publication_status"].startswith("DRAFT")
            for metadata in stored["metadatas"]
            if metadata["document_id"] in {"DOC09", "DOC10"}
        )
    code = (
        "import sys; from proyek_certan.knowledge.vector_store import VectorStore; "
        "store=VectorStore(sys.argv[1]); print(store.count()); store.close()"
    )
    reopened = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)],
        capture_output=True, text=True, check=True,
    )
    assert reopened.stdout.strip() == str(expected_count)
    with VectorStore(tmp_path) as store:
        results = KnowledgeRetriever(store, embedder).search("VLAN", top_k=3)
        assert len(results) == 3
        for result in results:
            assert result.text
            assert result.metadata["title"]
            assert result.metadata["section"]
            assert result.metadata["source_url"].startswith("https://")
            assert -1 <= result.similarity <= 1
