"""Real encoder, document mode and static-corpus abstention across reopen."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evaluation"))
from guard_candidate_cli_v3 import evaluate_scoped
from scope_candidate_v3 import GuardConfig

from proyek_certan.knowledge.embeddings import EmbeddingModel
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore

pytestmark = pytest.mark.skipif(
    os.environ.get("CERTAN_RUN_MODEL_TESTS") != "1",
    reason="Enable real model integration explicitly",
)


def test_real_scoped_search_preserves_source_and_rejects_live_state(tmp_path, chunks):
    embedder = EmbeddingModel()
    with VectorStore(tmp_path) as store:
        KnowledgeRetriever(store, embedder).index_chunks(chunks)
    with VectorStore(tmp_path) as reopened:
        retriever = KnowledgeRetriever(reopened, embedder)
        found = evaluate_scoped(
            retriever, chunks[0]["text"], top_k=3, config=GuardConfig(0.0, 0.0)
        )
        assert found.status == "ACCEPT"
        assert found.results[0].chunk_id == chunks[0]["chunk_id"]
        assert found.results[0].source == chunks[0]["metadata"]["source"]
        assert found.results[0].similarity == pytest.approx(1.0, abs=1e-5)
        assert len({r.document_id for r in found.results}) == len(found.results)
        live = evaluate_scoped(
            retriever, "Tampilkan status terbaru tiket TKT991122.", top_k=3
        )
        assert live.status == "ABSTAIN" and not live.results
        assert live.reason_codes == ("operational_data",)
