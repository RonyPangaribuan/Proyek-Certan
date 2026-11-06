"""Benchmark arithmetic and replay remain independent of archived runners."""
from pathlib import Path
import runpy
import pytest

benchmark = runpy.run_path(str(Path(__file__).resolve().parents[2] / "evaluation/benchmarks/final_pipeline.py"))
metrics = benchmark["metrics"]
ood_metrics = benchmark["ood_metrics"]


def test_multiple_relevant_documents_and_first_hit_rank():
    result = metrics(["DOC99", "DOC03", "DOC04", "DOC05", "DOC06"], {"DOC03", "DOC04"})
    assert result["recall@1"] == 0
    assert result["recall@3"] == 1
    assert result["precision@3"] == 2 / 3
    assert result["mrr"] == 1 / 2


def test_ood_has_undefined_recall_and_mrr():
    result = metrics(["DOC01"], set())
    assert result["recall@5"] is None and result["mrr"] is None
    assert result["precision@5"] == 0


def test_rejection_precision_counts_rejected_positives_as_errors():
    rows = [dict(relevant_documents=["a"], top1_similarity=.4),
            dict(relevant_documents=["a"], top1_similarity=.8),
            dict(relevant_documents=[], top1_similarity=.3),
            dict(relevant_documents=[], top1_similarity=.7)]
    result = ood_metrics(rows, .5)
    assert result["far"] == result["frr"] == .5
    assert result["rejection_precision"] == result["ood_rejection_rate"] == .5
    assert ood_metrics(rows, 0)["rejection_precision"] is None


def test_original_baseline_replays_without_historical_corpus():
    result = benchmark["verify_history"]()
    assert result["status"] == "PASS"
    assert result["final_test_baseline"]["recall@3"] == pytest.approx(22 / 24)
    assert result["historical_ood_diagnostic"]["false_acceptance_count"] == 18
    assert not result["rejected_candidates"]["guard_adopted"]
