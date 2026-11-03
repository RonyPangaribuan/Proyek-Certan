"""Real persistent ChromaDB tests with small, deterministic vectors."""

import json
import subprocess
import sys

import numpy as np
import pytest

from proyek_certan.knowledge.vector_store import VectorStore, VectorStoreError


def test_upsert_retains_metadata_and_updates_same_id_without_duplicates(tmp_path, chunks):
    chunk = chunks[0]
    with VectorStore(tmp_path) as store:
        assert store.upsert([chunk], [[1, 0, 0]]) == 1
        assert store.upsert([chunk], [[1, 0, 0]]) == 1
        assert store.count() == 1
        changed = {**chunk, "text": "Periksa DNS baru.", "metadata": {**chunk["metadata"], "section": "Revisi"}}
        store.upsert([changed], [[0, 1, 0]])
        found = store.query([[0, 1, 0]], top_k=10)
        assert found["ids"] == [[chunk["chunk_id"]]]
        assert found["documents"] == [[changed["text"]]]
        assert found["metadatas"] == [[changed["metadata"]]]
        assert found["distances"][0][0] == pytest.approx(0.0)
        assert store.count() == 1


def test_database_survives_client_close_and_reopen(tmp_path, chunks):
    with VectorStore(tmp_path) as store:
        store.upsert(chunks[:3], np.eye(3))
    with VectorStore(tmp_path) as reopened:
        assert reopened.count() == 3
        found = reopened.query([[1, 0, 0]])
        assert found["ids"][0][0] == chunks[0]["chunk_id"]
        assert found["metadatas"][0][0] == chunks[0]["metadata"]


def test_database_survives_writer_process_exit(tmp_path, chunks):
    code = "\n".join([
        "import json, sys",
        "from proyek_certan.knowledge.vector_store import VectorStore",
        "with VectorStore(sys.argv[1]) as store:",
        "    store.upsert(json.loads(sys.argv[2]), [[1, 0, 0]])",
    ])
    completed = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path), json.dumps(chunks[:1])],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    with VectorStore(tmp_path) as reopened:
        assert reopened.count() == 1
        assert reopened.query([[1, 0, 0]])["ids"] == [[chunks[0]["chunk_id"]]]


@pytest.mark.parametrize("vectors", [[], [[1, 0]], [[0, 0, 0]] * 2, [[float("nan"), 1, 0]] * 2])
def test_invalid_vectors_do_not_write(tmp_path, chunks, vectors):
    with VectorStore(tmp_path) as store:
        with pytest.raises(ValueError):
            store.upsert(chunks[:2], vectors)
        assert store.count() == 0


def test_reject_duplicate_ids_in_one_batch(tmp_path, chunks):
    with VectorStore(tmp_path) as store:
        with pytest.raises(ValueError, match="unique"):
            store.upsert([chunks[0], chunks[0]], [[1, 0], [0, 1]])
        assert store.count() == 0


def test_reject_wrong_dimension_without_corrupting_collection(tmp_path, chunks):
    with VectorStore(tmp_path) as store:
        store.upsert(chunks[:1], [[1, 0, 0]])
        with pytest.raises(VectorStoreError):
            store.upsert(chunks[1:2], [[1, 0]])
        with pytest.raises(VectorStoreError):
            store.query([[1, 0]])
        assert store.count() == 1


def test_reject_model_mismatch_after_reopen(tmp_path, chunks):
    with VectorStore(tmp_path) as store:
        store.upsert(chunks[:1], [[1, 0]])
    with pytest.raises(ValueError, match="embedding model"):
        VectorStore(tmp_path, model_name="a-different-model")


def test_reject_non_cosine_collection(tmp_path):
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(str(tmp_path), settings=Settings(anonymized_telemetry=False))
    try:
        client.create_collection("certan_knowledge", embedding_function=None)
    finally:
        client.close()
    with pytest.raises(ValueError, match="cosine"):
        VectorStore(tmp_path)


def test_empty_collection_and_closed_store(tmp_path):
    store = VectorStore(tmp_path)
    assert store.query([[1, 0, 0]])["ids"] == [[]]
    store.close()
    store.close()
    with pytest.raises(VectorStoreError, match="closed"):
        store.count()
