"""Validate mapping integration, exact cosine scores, and search edge cases."""

import pytest

from proyek_certan.knowledge.models import KnowledgeChunk
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


def test_search_converts_cosine_distance_and_preserves_source(tmp_path, chunks, embedder):
    with VectorStore(tmp_path) as store:
        retriever = KnowledgeRetriever(store, embedder)
        assert retriever.index_chunks(chunks[:3]) == 3
        retriever.index_chunks(chunks[:3])
        assert store.count() == 3
        results = retriever.search("WiFi bermasalah", top_k=20)
        assert [item.chunk_id for item in results] == [item["chunk_id"] for item in chunks[:3]]
        assert [item.similarity for item in results] == pytest.approx([1.0, 0.0, -1.0])
        assert results[0].text == chunks[0]["text"]
        assert results[0].source == chunks[0]["metadata"]["source"]
        assert results[0].metadata == chunks[0]["metadata"]
        filtered = retriever.search("WiFi bermasalah", relevance_threshold=0.5)
        assert [item.chunk_id for item in filtered] == [chunks[0]["chunk_id"]]
        assert len(retriever.search("WiFi", relevance_threshold=0.0)) == 2


def test_empty_collection_does_not_load_encoder(tmp_path, embedder):
    with VectorStore(tmp_path) as store:
        retriever = KnowledgeRetriever(store, embedder)
        assert retriever.search("WiFi tidak tersambung") == []
        assert retriever.index_chunks([]) == 0
        assert embedder.calls == 0


@pytest.mark.parametrize("query", ["", " \n ", None])
def test_empty_query_is_rejected_even_on_empty_collection(tmp_path, embedder, query):
    with VectorStore(tmp_path) as store:
        with pytest.raises(ValueError, match="query"):
            KnowledgeRetriever(store, embedder).search(query)
        assert embedder.calls == 0


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True])
def test_invalid_top_k(tmp_path, embedder, top_k):
    with VectorStore(tmp_path) as store:
        with pytest.raises(ValueError, match="top_k"):
            KnowledgeRetriever(store, embedder).search("wifi", top_k=top_k)


@pytest.mark.parametrize("threshold", [-1.1, 1.1, float("nan"), float("inf"), True, "0.5"])
def test_invalid_threshold(tmp_path, embedder, threshold):
    with VectorStore(tmp_path) as store:
        with pytest.raises(ValueError, match="relevance_threshold"):
            KnowledgeRetriever(store, embedder).search("wifi", relevance_threshold=threshold)


def test_query_encoder_must_match_document_encoder(tmp_path, embedder):
    embedder.model_name = "different-model"
    with VectorStore(tmp_path) as store:
        with pytest.raises(ValueError, match="must match"):
            KnowledgeRetriever(store, embedder)


@pytest.mark.parametrize("metadata", [{}, {"source": " "}, {"source": "a.pdf", "nested": {}}, {"source": "a.pdf", "value": float("nan")}])
def test_invalid_metadata_is_rejected(metadata):
    with pytest.raises((ValueError, TypeError)):
        KnowledgeChunk("a-001", "text", metadata)


def test_invalid_chunk_batch_is_rejected_before_encoding(tmp_path, embedder, chunks):
    with VectorStore(tmp_path) as store:
        retriever = KnowledgeRetriever(store, embedder)
        with pytest.raises(ValueError, match="Missing chunk field"):
            retriever.index_chunks([chunks[0], {"text": "Missing fields"}])
        assert embedder.calls == 0
        assert store.count() == 0
