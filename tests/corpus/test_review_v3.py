"""Whitespace safety and page provenance must be exact, never guessed."""

from pathlib import Path

import pytest

from proyek_certan.corpus.review_v3 import revise_v3, exact_page_span, page_word_index

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "doc_id,name",
    [
        ("DOC11", "DOC11_Incident_Management_UCF"),
        ("DOC13", "DOC13_Network_Administration"),
    ],
)
def test_v3_reflow_preserves_every_source_token(doc_id, name):
    original = (ROOT / f"data/corpus/processed/reviewed-v2/{name}.txt").read_text(
        encoding="utf-8"
    )
    revised, operations = revise_v3(doc_id, original)
    assert revised.split() == original.split()
    assert operations["changed"] and operations["line_breaks_joined"] > 0
    if doc_id == "DOC11":
        assert (
            original[original.index("Figure 1.1\n") :]
            == revised[revised.index("Figure 1.1\n") :]
        )
        assert "No other parties have the authority" in revised
    else:
        assert "5.3.1. No Wi-Fi infrastructure" in revised
        assert (
            "Vice Provost for Information Technology & Chief Information Officer\n"
            in revised
        )


def test_exact_page_alignment_does_not_guess_repeated_text():
    assert exact_page_span("same", "title", (["same", "same"], [1, 2])) == {}
    assert exact_page_span("missing", "title", (["same"], [1])) == {}
    span = exact_page_span(
        "last first", "title", (["start", "last", "first", "end"], [1, 1, 2, 2])
    )
    assert span["page_start"] == 1 and span["page_end"] == 2
    assert span["source_word_start"] == 1 and span["source_word_end_exclusive"] == 3


def test_real_source_page_alignment_matches_verified_objectives():
    index = page_word_index(
        ROOT / "data/corpus/raw/DOC11_Incident_Management_UCF.pdf", "DOC11"
    )
    assert (
        exact_page_span(
            "III. DEFINITIONS Incident: Implies something is broken", "title", index
        )["page_start"]
        == 2
    )


def test_unreviewed_anchor_drift_stops_reflow():
    with pytest.raises(ValueError, match="anchor"):
        revise_v3("DOC13", "# Different upstream source\n")
