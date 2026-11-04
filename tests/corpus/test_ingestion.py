"""Offline checks for cleaning, section-aware word chunking, and manifest ingestion."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import pytest

from proyek_certan.corpus.chunking import (
    Section, chunk_document, chunk_section, group_short_sections, split_sections,
)
from proyek_certan.corpus.cleaning import normalize_text
from proyek_certan.corpus.ingestion import build_chunks, load_corpus
from proyek_certan.knowledge.models import validate_chunks


def test_cleaning_preserves_headings_steps_commands_and_order():
    original = "# Title\r\n1. Check\u00a0the port  \r\n2. Run ovs-vsctl\r\n\r\n\r\nResult\r\n"
    cleaned = normalize_text(original)
    assert cleaned == "# Title\n1. Check the port\n2. Run ovs-vsctl\n\nResult\n"
    assert normalize_text(cleaned) == cleaned


def test_sections_use_headings_and_questions_but_not_numbered_steps():
    text = "# Title\nIntro\n## Procedure\n1. Check the cable.\n2. Run test.\nQ: Why?\nA: Verify VLAN.\n"
    sections = split_sections(text, "Fallback")
    assert [section.title for section in sections] == ["Title", "Procedure", "Why?"]
    assert "1. Check the cable.\n2. Run test." in sections[1].text


def test_word_limit_overlap_and_reconstruction_of_original_order():
    text = " ".join(f"w{i}" for i in range(53))
    parts = chunk_section(Section("Test", text), size=20, overlap=4)
    tokenized = [part.split() for part in parts]
    assert all(len(part) <= 20 for part in tokenized)
    assert all(tokenized[index - 1][-4:] == tokenized[index][:4] for index in range(1, len(parts)))
    rebuilt = tokenized[0] + [word for part in tokenized[1:] for word in part[4:]]
    assert rebuilt == text.split()


def test_paragraph_boundary_precedes_word_cut_when_available():
    section = Section("Test", "\n".join(" ".join(f"{line}{i}" for i in range(10)) for line in "abc"))
    parts = chunk_section(section, size=22, overlap=2)
    assert parts[0].split()[-1] == "b9"
    assert parts[1].split()[:2] == ["b8", "b9"]


def test_adjacent_short_sections_keep_headings_and_original_word_order():
    text = "# Guide\nIntro text\n## First\nCheck port\n## Second\nRetest link\n"
    groups = group_short_sections(split_sections(text, "Guide"), size=20)
    assert len(groups) == 1
    chunks = chunk_document(
        text, document_id="DOC98", source="DOC98.pdf", title="Guide",
        source_url="https://example.org/guide", size=20, overlap=4,
    )
    restored = chunks[0].text.split()
    for chunk in chunks[1:]:
        restored.extend(chunk.text.split()[4:])
    assert restored == text.split()


def test_short_document_has_one_unique_index_ready_chunk():
    chunks = chunk_document(
        "# Short\n1. Check port.\n2. Retest.", document_id="DOC99",
        source="DOC99.pdf", title="Short", source_url="https://example.org/doc",
    )
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "DOC99-0000"
    assert chunks[0].metadata == {
        "document_id": "DOC99", "source": "DOC99.pdf", "title": "Short",
        "section": "Short", "chunk_index": 0, "source_url": "https://example.org/doc",
    }
    assert validate_chunks([asdict(chunk) for chunk in chunks]) == chunks


def test_manifest_ingestion_checks_sha_and_produces_unique_ids(tmp_path: Path):
    processed = tmp_path / "data/corpus/processed"
    processed.mkdir(parents=True)
    evaluation = tmp_path / "evaluation"
    evaluation.mkdir()
    manifest = {"documents": []}
    report = {"documents": []}
    for doc_id in ("DOC01", "DOC02"):
        path = processed / f"{doc_id}.txt"
        text = "# Network\n" + " ".join(f"token{i}" for i in range(35)) + "\n"
        path.write_text(text, encoding="utf-8")
        relative = f"data/corpus/processed/{path.name}"
        manifest["documents"].append({
            "document_id": doc_id, "filename": f"{doc_id}.pdf", "title": "Network",
            "source_url": f"https://example.org/{doc_id}", "text_file": relative,
            "source_status": "processed_official_html",
        })
        report["documents"].append({
            "document_id": doc_id, "text_file": relative, "status": "processed",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "character_count": len(text),
        })
    (tmp_path / "data/corpus/corpus_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (evaluation / "corpus_processing.json").write_text(json.dumps(report), encoding="utf-8")
    chunks, audit = build_chunks(tmp_path, size=20, overlap=4)
    chunks_again, _ = build_chunks(tmp_path, size=20, overlap=4)
    assert audit["summary"]["document_count"] == 2
    assert {chunk.metadata["document_id"] for chunk in chunks} == {"DOC01", "DOC02"}
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
    assert [chunk.chunk_id for chunk in chunks] == [chunk.chunk_id for chunk in chunks_again]
    assert max(len(chunk.text.split()) for chunk in chunks) <= 20
    (processed / "DOC01.txt").write_text("# Tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        load_corpus(tmp_path)
