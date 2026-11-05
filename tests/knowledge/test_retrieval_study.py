"""Evaluation arithmetic, leakage barriers and metadata experiment contracts."""

import json
import sys
from pathlib import Path

import pytest

from proyek_certan.knowledge.models import SearchResult

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evaluation"))
from metadata_intent_candidate import query_intent, rank_documents
from retrieval_study import (
    paired_difference,
    rule_path,
    select_threshold,
    sha,
    summary,
    wilson,
)


def result(doc, score, kind):
    return SearchResult(
        doc, "example", "source", {"document_id": doc, "document_kind": kind}, score
    )


def row(q, split, docs, score, ranking):
    from benchmark_semantic_retrieval import metrics

    return {
        "id": q,
        "split": split,
        "relevant_documents": docs,
        "documents": [{"document_id": d, "similarity": score} for d in ranking],
        "metrics": metrics(ranking, set(docs)),
    }


def test_document_dedup_best_chunk_and_intent_do_not_change_cosine():
    found = [
        result("random-policy", 0.74, "network_policy"),
        result("random-guide", 0.68, "diagnostic"),
        result("random-policy", 0.73, "network_policy"),
    ]
    assert [r.chunk_id for r in rank_documents(found)] == [
        "random-policy",
        "random-guide",
    ]
    changed = rank_documents(found, query="Bagaimana diagnosis koneksi gagal?")
    assert [r.chunk_id for r in changed] == ["random-guide", "random-policy"]
    assert [r.similarity for r in changed] == [0.68, 0.74]
    assert (
        rank_documents(found, query="Apa izin kebijakan jaringan?")[0].chunk_id
        == "random-policy"
    )
    assert (
        query_intent("Apakah kebijakan melarang ini dan bagaimana cek koneksi gagal?")
        is None
    )
    assert query_intent("Tolong jelaskan layanan") is None


def test_gate_uses_selected_document_raw_score_and_counts_rejections_as_zero():
    rows = [
        row("good", "development", ["A"], 0.7, ["A", "B", "C"]),
        row("low", "development", ["A"], 0.4, ["A", "B", "C"]),
        row("ood", "development", [], 0.6, ["B", "C", "A"]),
    ]
    s = summary(rows, 0.65)
    assert s["false_acceptance_count"] == 0
    assert s["false_rejection_count"] == 1
    assert s["false_rejection_rate"] == 0.5
    assert s["metrics"]["recall@3"] == 0.5
    assert s["metrics"]["precision@3"] == pytest.approx(1 / 6)
    assert s["accepted_correct_top1_fraction"] == 1


def test_threshold_selection_uses_development_only_with_deterministic_tie_rule():
    rows = [
        row("p", "development", ["A"], 0.7, ["A"]),
        row("o", "development", [], 0.3, ["A"]),
    ]
    threshold, curve = select_threshold(rows, [0.0, 0.3, 0.4, 0.5, 0.8])
    assert threshold == 0.4
    assert len(curve) == 5
    with pytest.raises(ValueError, match="development"):
        select_threshold([dict(r, split="evaluation") for r in rows], [0.5])


def test_paired_comparison_requires_matching_labels_and_known_delta():
    a = [row("p", "evaluation", ["A"], 0.7, ["B", "A"])]
    b = [row("p", "evaluation", ["A"], 0.7, ["A", "B"])]
    assert paired_difference(a, b)["mrr"]["bootstrap95"] == [0.5, 0.5]
    with pytest.raises(ValueError, match="labels"):
        paired_difference(a, [dict(b[0], relevant_documents=["B"])])
    low, high = wilson(0, 12)
    assert low == pytest.approx(0, abs=1e-10) and high > 0.24


def test_frozen_labels_baseline_and_preregistered_rules_are_unchanged():
    protocol = json.loads(
        (ROOT / "evaluation/retrieval_study_protocol_v2.json").read_text(
            encoding="utf-8"
        )
    )
    assert (
        sha(ROOT / "evaluation/retrieval_study_labels_v2.json")
        == protocol["labels_sha256"]
    )
    for path, expected in protocol["frozen_baseline_sha256"].items():
        assert sha(ROOT / path) == expected
    for key in ("rules", "metadata_rule"):
        assert (
            sha(rule_path(protocol["candidate"][f"{key}_file"]))
            == protocol["candidate"][f"{key}_sha256"]
        )
    labels = json.loads(
        (ROOT / "evaluation/retrieval_study_labels_v2.json").read_text(encoding="utf-8")
    )["queries"]
    for split in ("development", "evaluation"):
        subset = [q for q in labels if q["split"] == split]
        assert len(subset) == 30
        assert sum(bool(q["relevant_documents"]) for q in subset) == 18
