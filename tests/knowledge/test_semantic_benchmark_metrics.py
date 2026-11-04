"""Check document-level benchmark arithmetic without loading the model."""

from pathlib import Path
import runpy


metrics = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "evaluation/benchmark_semantic_retrieval.py")
)["metrics"]


def test_multiple_relevant_documents_and_first_hit_rank() -> None:
    result = metrics(["DOC99", "DOC03", "DOC04", "DOC05", "DOC06"], {"DOC03", "DOC04"})
    assert result["recall@1"] == 0
    assert result["recall@3"] == 1
    assert result["precision@3"] == 2 / 3
    assert result["mrr"] == 1 / 2


def test_out_of_domain_has_undefined_recall_and_mrr() -> None:
    result = metrics(["DOC01", "DOC02", "DOC03", "DOC04", "DOC05"], set())
    assert result["recall@5"] is None
    assert result["precision@5"] == 0
    assert result["mrr"] is None
