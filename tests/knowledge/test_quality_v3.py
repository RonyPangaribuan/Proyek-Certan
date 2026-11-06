"""Gate arithmetic, split barriers, pairing and title-mixture contracts."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evaluation"))
from quality_v3 import (
    summarize,
    paired,
    verify_baseline,
    locked_code_path,
    sha,
    read,
    OUT,
)
from title_candidate_v3 import rank_titles
from proyek_certan.knowledge.documents import distinct_documents
from proyek_certan.knowledge.models import SearchResult


def row(id, positive, status, correct=True):
    return dict(
        id=id,
        relevant_documents=["A"] if positive else [],
        status=status,
        documents=[dict(document_id="A" if correct else "B")],
        category="sample",
        latency_ms=1,
        gated={
            m: float(status == "ACCEPT" and correct)
            for m in ("precision@1", "precision@3", "recall@3", "recall@5", "mrr")
        },
        ungated={
            m: float(correct)
            for m in ("precision@1", "precision@3", "recall@3", "recall@5", "mrr")
        },
    )


def test_low_confidence_is_rejection_and_ood_is_not_positive_recall():
    result = summarize([row("p", True, "LOW_CONFIDENCE"), row("o", False, "ABSTAIN")])
    assert result["frr"] == 1 and result["far"] == 0
    assert result["gated"]["recall@3"] == 0
    assert result["ood_rejection_rate"] == 1 and result["positive_acceptance_rate"] == 0


def test_paired_error_ci_and_identical_labels_are_required():
    a = [row("p", True, "ACCEPT"), row("o", False, "ACCEPT")]
    b = [row("p", True, "ACCEPT"), row("o", False, "ABSTAIN")]
    assert paired(a, b)["far"]["bootstrap95"] == [-1, -1]
    b[0]["relevant_documents"] = ["B"]
    with pytest.raises(ValueError, match="ground truth"):
        paired(a, b)


def test_title_score_mixture_keeps_original_cosine():
    found = distinct_documents(
        [
            SearchResult("a", "text", "s", {"document_id": "first"}, 0.8),
            SearchResult("b", "text", "s", {"document_id": "second"}, 0.7),
        ]
    )
    ranked = rank_titles(found, {"first": 0.1, "second": 0.9}, 0.4)
    assert ranked[0].document_id == "second"
    assert ranked[0].similarity == 0.7
    assert ranked[0].ranking_score == pytest.approx(0.78)


def test_historical_corpus_and_all_75_labels_stay_frozen():
    assert len(verify_baseline()["baseline_sha256"]) >= 70


def test_archiving_does_not_change_the_measured_candidate_implementation():
    lock = read(OUT / "lock-r2.json")
    for original, expected in lock["code_sha256"].items():
        assert sha(locked_code_path(original)) == expected
    assert (
        sha(OUT.parent / "scope_candidate_v3.py")
        == lock["code_sha256"]["src/proyek_certan/knowledge/scope.py"]
    )
