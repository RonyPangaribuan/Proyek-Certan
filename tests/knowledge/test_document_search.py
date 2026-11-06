"""Document identity, max aggregation, cache invalidation and CLI contracts."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evaluation"))
from guard_candidate_cli_v3 import evaluate_scoped, main as experimental_main

from proyek_certan.knowledge.documents import distinct_documents
from proyek_certan.knowledge.models import SearchResult
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore
from proyek_certan.knowledge.cli import main


def test_distinct_documents_use_best_chunk_and_stable_ties():
    def r(chunk, doc, score):
        return SearchResult(
            chunk, "text", "test.pdf", {"document_id": doc, "section": "section"}, score
        )

    found = distinct_documents(
        [r("a1", "a", 0.6), r("b1", "b", 0.7), r("a2", "a", 0.8), r("c1", "c", 0.7)]
    )
    assert [x.document_id for x in found] == ["a", "b", "c"]
    assert found[0].chunk_id == "a2" and found[0].candidate_chunk_count == 2
    assert found[0].similarity == found[0].ranking_score == 0.8
    assert found[0].section == "section"


def test_missing_document_identity_is_not_invented():
    with pytest.raises(ValueError, match="document_id"):
        distinct_documents([SearchResult("c", "text", "x.pdf", {}, 0.8)])


def test_document_retrieval_and_scoped_reopen(tmp_path, chunks, embedder):
    with VectorStore(tmp_path) as store:
        retriever = KnowledgeRetriever(store, embedder)
        retriever.index_chunks(chunks)
        assert len(retriever.catalog().documents) == 5
        retriever.index_chunks(chunks[:1])
        assert retriever._catalog is None
    with VectorStore(tmp_path) as reopened:
        retriever = KnowledgeRetriever(reopened, embedder)
        docs = retriever.search_documents("WiFi", top_k=3, candidate_depth=5)
        assert len({d.document_id for d in docs}) == 3
        result = evaluate_scoped(
            retriever, "Berapa alamat IP laptop saya saat ini?", top_k=3
        )
        assert result.status == "ABSTAIN" and result.results == ()


def test_empty_cli_scoped_output_is_actionable(tmp_path, capsys):
    assert experimental_main(["--db", str(tmp_path), "--query", "WiFi"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert (
        result["status"] == "ABSTAIN" and result["reasons"] and result["results"] == []
    )
    assert result["experiment_only"] and result["adopted"] is False


def test_document_cli_rejects_chunk_filter_ambiguity(tmp_path, capsys):
    assert (
        main(
            [
                "search",
                "--db",
                str(tmp_path),
                "--query",
                "WiFi",
                "--document-level",
                "--relevance-threshold",
                "0.5",
            ]
        )
        == 2
    )
    assert "no adopted abstention policy" in capsys.readouterr().err


def test_failed_guard_is_unavailable_in_final_runtime(tmp_path):
    assert not hasattr(KnowledgeRetriever, "search_scoped")
    with pytest.raises(SystemExit):
        main(["search", "--db", str(tmp_path), "--query", "WiFi", "--scope-guard"])
