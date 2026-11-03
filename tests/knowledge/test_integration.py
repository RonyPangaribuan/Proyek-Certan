"""Opt-in real multilingual model + persistent ChromaDB integration tests."""

import os

import numpy as np
import pytest

from proyek_certan.knowledge.embeddings import EmbeddingModel
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


pytestmark = pytest.mark.skipif(
    os.environ.get("CERTAN_RUN_MODEL_TESTS") != "1",
    reason="Set CERTAN_RUN_MODEL_TESTS=1 to run/download the real sentence-transformers model",
)


@pytest.fixture(scope="module")
def real_model():
    return EmbeddingModel()


def test_real_model_encodes_three_incident_texts(real_model, chunks):
    matrix = real_model.encode([chunk["text"] for chunk in chunks[:3]])
    assert matrix.shape == (3, 384)
    assert real_model.dimension == 384
    assert np.isfinite(matrix).all()
    assert np.linalg.norm(matrix, axis=1) == pytest.approx([1, 1, 1], abs=1e-5)
    single = real_model.encode("Koneksi LAN terputus")
    assert single.shape == (1, 384)


def test_real_semantic_search_reindex_and_reopen(tmp_path, real_model, chunks):
    with VectorStore(tmp_path) as store:
        retriever = KnowledgeRetriever(store, real_model)
        assert retriever.index_chunks(chunks) == 5
        assert retriever.index_chunks(chunks) == 5
        assert store.count() == 5
    with VectorStore(tmp_path) as reopened:
        retriever = KnowledgeRetriever(reopened, real_model)
        results = retriever.search("Kabel LAN putus dan port switch bermasalah", top_k=3)
        assert len(results) == 3
        assert results[0].chunk_id == "dummy-lan-001"
        assert results[0].source == "dummy_sop_lan.txt"
        assert results[0].metadata["document_id"] == "dummy-lan"
        assert all(-1 <= result.similarity <= 1 for result in results)
        exact = retriever.search(chunks[0]["text"], top_k=1)
        assert exact[0].chunk_id == chunks[0]["chunk_id"]
        assert exact[0].similarity == pytest.approx(1.0, abs=1e-5)
