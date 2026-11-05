"""Check document-level benchmark arithmetic without loading the model."""

from pathlib import Path
import hashlib
import json
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


def test_saved_benchmark_matches_frozen_labels_and_abstention() -> None:
    root = Path(__file__).resolve().parents[2]
    label_file = root / "evaluation/semantic_retrieval_ground_truth.json"
    labels = json.loads(label_file.read_text(encoding="utf-8"))["queries"]
    report = json.loads((root / "evaluation/semantic_retrieval_benchmark.json").read_text(encoding="utf-8"))
    assert report["ground_truth_sha256"] == hashlib.sha256(label_file.read_bytes()).hexdigest()
    assert len(labels) == 15
    for profile in report["profiles"].values():
        assert len(profile["queries"]) == 15
        for label, row in zip(labels, profile["queries"], strict=True):
            assert row["id"] == label["id"]
            assert row["relevant_documents"] == label["relevant_documents"]
            assert row["metrics"] == metrics(row["distinct_document_ranking"],
                                              set(label["relevant_documents"]))
            if label["type"] == "out_of_domain":
                assert row["metrics"]["recall@3"] is None
                assert row["metrics"]["mrr"] is None
        threshold = next(item for item in profile["threshold_analysis"] if item["threshold"] == 0.5)
        assert threshold["accepted_relevant_queries"] == 12
        assert threshold["accepted_ood_queries"] == []
