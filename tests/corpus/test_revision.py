"""Safety properties of the source-specific corpus revision."""

import json
import hashlib
from pathlib import Path

import pytest

from proyek_certan.corpus.revision import document_kind, revise_text

ROOT = Path(__file__).resolve().parents[2]


def test_reviewed_changes_preserve_words_except_verified_page_furniture():
    manifest = json.loads(
        (ROOT / "data/corpus/corpus_manifest.json").read_text(encoding="utf-8")
    )
    for doc in manifest["documents"]:
        original = (ROOT / doc["text_file"]).read_text(encoding="utf-8")
        revised, info = revise_text(doc["document_id"], original)
        assert info["changed"] == (doc["document_id"] in {"DOC06", "DOC11", "DOC13"})
        if doc["document_id"] == "DOC06":
            assert revised.split() == original.split()
            assert not any(
                line.count("$ ovs-vsctl") > 1 for line in revised.splitlines()
            )
        elif doc["document_id"] == "DOC11":
            kept = [
                line
                for line in original.splitlines()
                if line not in {str(i) for i in range(1, 17)}
            ]
            assert revised.split() == "\n".join(kept).split()
            assert "No other parties have the authority" in revised
            assert "Priority Business Impact Urgency Response Resolution" in revised
        elif doc["document_id"] == "DOC13":
            assert (
                revised.split()
                == original.replace(
                    "University Policy 08-010 University Network Administration\n", ""
                ).split()
            )
            assert "5.3.1. No Wi-Fi infrastructure" in revised
        else:
            assert revised == original
        if doc["document_id"] in {"DOC09", "DOC10"}:
            assert "DRAFT" in revised and "[Diisi" in revised


@pytest.mark.parametrize("doc_id", ["DOC06", "DOC11", "DOC13"])
def test_unreviewed_source_drift_fails_instead_of_silent_rewrite(doc_id):
    with pytest.raises(ValueError, match="audit"):
        revise_text(doc_id, "# Changed upstream\nnew content\n")


def test_source_purpose_classification_does_not_use_document_ids():
    assert document_kind("Wireless troubleshooting guidance") == "diagnostic"
    assert (
        document_kind("UCF IT Incident Management Policy & Procedure")
        == "incident_procedure"
    )
    assert document_kind("Network Acceptable Use Policy") == "network_policy"


def test_reviewed_metadata_points_to_verified_revision_and_keeps_historical_url():
    correction = json.loads(
        (ROOT / "evaluation/source_provenance_v2.json").read_text(encoding="utf-8")
    )["documents"]["DOC13"]
    raw = ROOT / "data/corpus/raw/DOC13_Network_Administration.pdf"
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == correction["source_pdf_sha256"]
    report = json.loads(
        (ROOT / "evaluation/reviewed_corpus_v2.json").read_text(encoding="utf-8")
    )
    for profile in report["profiles"].values():
        chunks = json.loads((ROOT / profile["chunk_file"]).read_text(encoding="utf-8"))
        selected = [c for c in chunks if c["metadata"]["document_id"] == "DOC13"]
        assert selected
        for chunk in selected:
            metadata = chunk["metadata"]
            assert metadata["source_url"] == correction["verified_source_url"]
            assert metadata["historical_source_url"] == correction["historical_source_url"]
            assert metadata["source_revision"] == "2024-08-06"
            assert metadata["source_pdf_sha256"] == correction["source_pdf_sha256"]
