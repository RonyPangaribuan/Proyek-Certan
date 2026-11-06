"""Query dependency and abstention contracts; no real model required."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evaluation"))

from proyek_certan.knowledge.documents import CorpusCatalog, distinct_documents
from proyek_certan.knowledge.models import SearchResult
from scope_candidate_v3 import (
    GuardConfig,
    ScopeGuard,
    unavailable_dependency,
)


def catalog():
    return CorpusCatalog(
        [
            {
                "document_id": "arbitrary-a",
                "title": "Wireless troubleshooting",
                "source": "a.pdf",
                "publisher": "Microsoft Learn",
            },
            {
                "document_id": "arbitrary-b",
                "title": "Incident policy",
                "source": "b.pdf",
                "publisher": "University of Central Florida Information Technology",
            },
        ]
    )


@pytest.mark.parametrize(
    "query",
    [
        "WiFi saya sedang putus; bagaimana langkah diagnosis?",
        "Bagaimana cara memeriksa alamat IP komputer saya sekarang?",
        "Apa langkah mengumpulkan data paket ketika jaringan kampus gagal hari ini?",
        "Menurut UCF apa beda incident dan request?",
        "Menurut University of Central Florida apa beda incident dan request?",
    ],
)
def test_local_or_live_words_do_not_block_generic_knowledge(query):
    assert unavailable_dependency(query, catalog()) is None


@pytest.mark.parametrize(
    "query,scope",
    [
        ("Berapa alamat IP komputer saya sekarang?", "operational_data"),
        ("Tampilkan status tiket TKT-773301.", "operational_data"),
        ("Siapa teknisi piket malam ini?", "operational_data"),
        ("Apa kebijakan VLAN Universitas Pelangi?", "unsupported_institution"),
        (
            "Apa aturan UCF dan Universitas Pelangi tentang WiFi?",
            "unsupported_institution",
        ),
    ],
)
def test_unavailable_dependencies_need_structural_evidence(query, scope):
    assert unavailable_dependency(query, catalog())[0] == scope


def test_raw_cosine_gate_is_separate_from_ranking_score_and_draft_warning():
    results = distinct_documents(
        [
            SearchResult(
                "c",
                "text",
                "a.pdf",
                {
                    "document_id": "d",
                    "source": "a.pdf",
                    "publication_status": "DRAFT",
                    "review_required": True,
                },
                0.6,
            )
        ]
    )
    decision = ScopeGuard(GuardConfig(0.5, 0.2)).evaluate(
        "Bagaimana prosedur insiden?", results, title_support=0.4, catalog=catalog()
    )
    assert decision.status == "ACCEPT" and decision.warnings and decision.results
    low = ScopeGuard(GuardConfig(0.7, 0.2)).evaluate(
        "Bagaimana prosedur insiden?", results, title_support=0.4, catalog=catalog()
    )
    assert low.status == "LOW_CONFIDENCE" and not low.results
    assert low.reason_codes == ("low_cosine",)


def test_abstention_and_empty_collection_have_no_presented_sources():
    guard = ScopeGuard()
    decision = guard.evaluate(
        "Berapa password akun saya sekarang?", [], title_support=None, catalog=catalog()
    )
    assert decision.status == "ABSTAIN" and not decision.results
    assert decision.scope == "operational_data"
    assert (
        guard.evaluate(
            "Bagaimana jaringan bekerja?", [], title_support=None, catalog=catalog()
        ).status
        == "ABSTAIN"
    )


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), 1.1, "0.5"])
def test_guard_rejects_invalid_config(value):
    with pytest.raises(ValueError):
        GuardConfig(value, 0.0)
