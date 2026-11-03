"""Exercise real PDFs and isolated failures without models, network, or OCR."""

import csv
import hashlib
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from proyek_certan.corpus import validation


def make_pdf(path: Path, texts: list[str | None], password: str | None = None) -> Path:
    writer = PdfWriter()
    for text in texts:
        page = writer.add_blank_page(width=612, height=792)
        if text is not None:
            font = DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            })
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
            })
            content = DecodedStreamObject()
            content.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii"))
            page[NameObject("/Contents")] = content
    if password is not None:
        writer.encrypt(password)
    writer.write(path)
    return path


def test_real_extraction_counts_and_empty_pages(tmp_path):
    text = "Network troubleshooting procedure. " * 5
    path = make_pdf(tmp_path / "sample.pdf", [text, None, "Cover"])
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    result = validation.validate_pdf(path, tmp_path)
    assert result.page_count == 3
    assert result.character_count == len(text) + len("Cover")
    assert result.empty_page_count == 1
    assert result.empty_page_numbers == [2]
    assert result.failed_page_numbers == []
    assert result.extraction_status == "success"
    assert result.readiness == "review"
    assert result.quality_issues == {"empty_text": [2], "sparse_text": [3]}
    assert result.sha256 == before == hashlib.sha256(path.read_bytes()).hexdigest()


def test_clean_pdf_is_ready(tmp_path):
    path = make_pdf(tmp_path / "clean.pdf", ["Readable network procedure. " * 10])
    result = validation.validate_pdf(path, tmp_path)
    assert result.extraction_status == "success"
    assert result.readiness == "ready"
    assert not result.quality_issues


@pytest.mark.parametrize("password,status", [(None, "no_text"), ("secret", "encrypted")])
def test_blank_or_password_protected_pdf_is_blocked(tmp_path, password, status):
    path = make_pdf(tmp_path / "blocked.pdf", [None], password)
    result = validation.validate_pdf(path, tmp_path)
    assert result.extraction_status == status
    assert result.readiness == "blocked"
    assert result.character_count == 0
    if password:
        assert result.page_count is None
        assert result.empty_page_count is None
        assert "Password required" in result.error
    else:
        assert result.empty_page_numbers == [1]


def test_empty_password_encryption_can_be_read(tmp_path):
    path = make_pdf(tmp_path / "encrypted.pdf", ["Readable network procedure. " * 10], "")
    assert validation.validate_pdf(path, tmp_path).extraction_status == "success"


def test_zero_page_pdf_is_blocked(tmp_path):
    path = make_pdf(tmp_path / "zero.pdf", [])
    result = validation.validate_pdf(path, tmp_path)
    assert result.page_count == 0
    assert result.extraction_status == "failed"
    assert result.error == "PDF contains no pages"


def test_corrupt_pdf_does_not_stop_other_documents(tmp_path):
    (tmp_path / "broken.pdf").write_bytes(b"not a PDF")
    make_pdf(tmp_path / "valid.PDF", ["Network procedure. " * 10])
    nested = tmp_path / "nested"
    nested.mkdir()
    make_pdf(nested / "valid.pdf", ["Other procedure. " * 10])
    (tmp_path / "ignore.txt").write_text("ignored")
    results = validation.validate_corpus(tmp_path)
    assert [item.relative_path for item in results] == ["broken.pdf", "nested/valid.pdf", "valid.PDF"]
    assert results[0].extraction_status == "failed"
    assert results[0].page_count is None
    assert results[0].empty_page_count is None
    assert results[0].error
    assert results[1].readiness == results[2].readiness == "ready"


def test_page_failure_is_distinct_from_empty_and_audit_continues(tmp_path, monkeypatch):
    path = tmp_path / "partial.pdf"
    path.write_bytes(b"placeholder")

    class BrokenPage:
        def extract_text(self):
            raise ValueError("bad content stream")

    pages = [
        SimpleNamespace(extract_text=lambda: "Readable network procedure. " * 10),
        BrokenPage(),
        SimpleNamespace(extract_text=lambda: None),
    ]
    monkeypatch.setattr(validation, "PdfReader", lambda *args, **kwargs: SimpleNamespace(
        is_encrypted=False, pages=pages,
    ))
    result = validation.validate_pdf(path, tmp_path)
    assert result.extraction_status == "partial"
    assert result.readiness == "blocked"
    assert result.empty_page_numbers == [3]
    assert result.empty_page_count == 1
    assert result.failed_page_numbers == [2]
    assert result.pages[1].is_empty is None
    assert result.pages[1].error == "ValueError: bad content stream"


def test_parser_warning_is_recorded_for_review(tmp_path, monkeypatch):
    path = tmp_path / "warning.pdf"
    path.write_bytes(b"placeholder")

    def extract():
        logging.getLogger("pypdf").warning("font mapping is incomplete")
        return "Readable network procedure. " * 10

    monkeypatch.setattr(validation, "PdfReader", lambda *args, **kwargs: SimpleNamespace(
        is_encrypted=False, pages=[SimpleNamespace(extract_text=extract)],
    ))
    result = validation.validate_pdf(path, tmp_path)
    assert result.extraction_status == "success"
    assert result.readiness == "review"
    assert result.parser_warnings == ["page 1: font mapping is incomplete"]


@pytest.mark.parametrize("text,issues", [
    (" \n\t", ["empty_text"]),
    ("Cover", ["sparse_text"]),
    ("abc\ufffd\x00\ue000(cid:12)", ["sparse_text", "replacement_characters",
                                     "unexpected_control_characters", "private_use_characters", "unmapped_glyphs"]),
    ("!" * 100, ["low_alphanumeric_ratio"]),
    ("A" * 80, []),
])
def test_text_quality_signals(text, issues):
    assert validation.inspect_text(text) == issues


def test_cli_exports_reports_and_detects_count_mismatch(tmp_path, capsys):
    source = tmp_path / "raw"
    source.mkdir()
    make_pdf(source / "valid.pdf", ["Readable network procedure. " * 10])
    output = tmp_path / "evaluation"
    args = ["--input-dir", str(source), "--output-dir", str(output)]
    assert validation.main(args + ["--expected-count", "1"]) == 0
    report = json.loads((output / "pdf_validation.json").read_text(encoding="utf-8"))
    with (output / "pdf_validation.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert report["summary"]["document_count_matches"] is True
    assert report["summary"]["readiness_counts"] == {"ready": 1}
    assert report["method"]["ocr_applied"] is False
    assert rows[0]["filename"] == "valid.pdf"
    assert int(rows[0]["character_count"]) == report["documents"][0]["character_count"]
    assert "| valid.pdf |" in capsys.readouterr().out
    assert validation.main(args + ["--expected-count", "2"]) == 2
    assert "Expected 2 PDFs, found 1" in capsys.readouterr().out


def test_cli_failure_exit_and_empty_corpus(tmp_path, capsys):
    source = tmp_path / "raw"
    source.mkdir()
    args = ["--input-dir", str(source), "--output-dir", str(tmp_path / "evaluation"),
            "--expected-count", "1"]
    assert validation.main(args) == 2
    make_pdf(source / "blank.pdf", [None])
    assert validation.main(args) == 1
    assert "no_text" in capsys.readouterr().out


def test_missing_directory_is_an_explicit_error(tmp_path):
    with pytest.raises(NotADirectoryError):
        validation.discover_pdfs(tmp_path / "missing")


def test_cli_rejects_invalid_threshold():
    with pytest.raises(SystemExit) as exc:
        validation.main(["--min-page-chars", "0"])
    assert exc.value.code == 2
