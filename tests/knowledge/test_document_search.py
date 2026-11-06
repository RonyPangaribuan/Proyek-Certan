"""Best-chunk aggregation, stable ties and persistent document retrieval."""
import pytest
from proyek_certan.knowledge.documents import distinct_documents
from proyek_certan.knowledge.models import SearchResult
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


def test_distinct_documents_use_best_chunk_and_stable_ties():
    def result(chunk, doc, score):
        return SearchResult(chunk, "text", "test.pdf", {"document_id": doc, "section": "section"}, score)
    found = distinct_documents([result("a1", "a", .6), result("b1", "b", .7),
                                result("a2", "a", .8), result("c1", "c", .7)])
    assert [x.document_id for x in found] == ["a", "b", "c"]
    assert found[0].chunk_id == "a2" and found[0].candidate_chunk_count == 2
    assert found[0].similarity == found[0].ranking_score == .8


def test_missing_document_identity_is_not_invented():
    with pytest.raises(ValueError, match="document_id"):
        distinct_documents([SearchResult("c", "text", "x.pdf", {}, .8)])


def test_document_retrieval_reopens_and_deduplicates(tmp_path, chunks, embedder):
    with VectorStore(tmp_path) as store:
        KnowledgeRetriever(store, embedder).index_chunks(chunks)
    with VectorStore(tmp_path) as reopened:
        docs = KnowledgeRetriever(reopened, embedder).search_documents("WiFi", top_k=3, candidate_depth=5)
        assert len({d.document_id for d in docs}) == 3
        assert all(d.ranking_score == d.similarity for d in docs)


def test_rejected_guard_is_not_part_of_runtime():
    assert not hasattr(KnowledgeRetriever, "search_scoped")
