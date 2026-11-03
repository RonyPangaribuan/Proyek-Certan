"""Validate PDF text extraction before ingestion; never modify PDFs or run OCR.

Run with ``uv run --frozen --no-sync python -m proyek_certan.corpus.validation``.
Character counts use the unmodified string returned by pypdf. Empty means
``not text.strip()``; extraction errors are recorded separately from empty pages.
Quality flags are heuristics for manual review, not proof of unusable content.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import unicodedata
import warnings
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pypdf
from pypdf import PdfReader


@dataclass
class PageValidation:
    page_number: int
    character_count: int = 0
    non_whitespace_characters: int = 0
    is_empty: bool | None = None
    quality_issues: list[str] = field(default_factory=list)
    text_preview: str = ""
    error: str | None = None


@dataclass
class DocumentValidation:
    filename: str
    relative_path: str
    sha256: str = ""
    page_count: int | None = None
    character_count: int = 0
    empty_page_count: int | None = None
    empty_page_numbers: list[int] = field(default_factory=list)
    failed_page_numbers: list[int] = field(default_factory=list)
    extraction_status: str = "failed"
    readiness: str = "blocked"
    quality_issues: dict[str, list[int]] = field(default_factory=dict)
    parser_warnings: list[str] = field(default_factory=list)
    error: str | None = None
    pages: list[PageValidation] = field(default_factory=list)


class _WarningCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.messages: list[str] = []
        self.page_number: int | None = None

    def emit(self, record: logging.LogRecord) -> None:
        context = f"page {self.page_number}: " if self.page_number else "document: "
        self.messages.append(context + record.getMessage())


def discover_pdfs(input_dir: Path) -> list[Path]:
    """Recursively discover PDFs, including uppercase extensions, in stable order."""
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Corpus directory does not exist: {input_dir}")
    return sorted(
        (path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf"),
        key=lambda path: path.relative_to(input_dir).as_posix().casefold(),
    )


def inspect_text(text: str, min_page_chars: int = 80) -> list[str]:
    """Conservative quality signals; sparse pages may be covers or diagrams."""
    if min_page_chars < 1:
        raise ValueError("min_page_chars must be positive")
    if not text.strip():
        return ["empty_text"]
    issues = []
    visible = [char for char in text if not char.isspace()]
    if len(visible) < min_page_chars:
        issues.append("sparse_text")
    if "\ufffd" in text:
        issues.append("replacement_characters")
    if any(unicodedata.category(char) == "Cc" and char not in "\n\r\t\f" for char in text):
        issues.append("unexpected_control_characters")
    if any(unicodedata.category(char) == "Co" for char in text):
        issues.append("private_use_characters")
    if re.search(r"\(cid:\d+\)", text):
        issues.append("unmapped_glyphs")
    if len(visible) >= min_page_chars and sum(char.isalnum() for char in visible) / len(visible) < 0.5:
        issues.append("low_alphanumeric_ratio")
    return issues


def validate_page(page: object, page_number: int, min_page_chars: int = 80) -> PageValidation:
    text = page.extract_text() or ""
    return PageValidation(
        page_number=page_number,
        character_count=len(text),
        non_whitespace_characters=sum(not char.isspace() for char in text),
        is_empty=not text.strip(),
        quality_issues=inspect_text(text, min_page_chars),
        text_preview=" ".join(text.split())[:180],
    )


def _finalize(result: DocumentValidation) -> None:
    result.character_count = sum(page.character_count for page in result.pages)
    result.empty_page_numbers = [page.page_number for page in result.pages if page.is_empty is True]
    result.failed_page_numbers = [page.page_number for page in result.pages if page.error]
    if result.page_count is not None:
        result.empty_page_count = len(result.empty_page_numbers)
    for page in result.pages:
        for issue in page.quality_issues:
            result.quality_issues.setdefault(issue, []).append(page.page_number)
    has_text = any(page.is_empty is False for page in result.pages)
    if result.extraction_status == "encrypted":
        return
    if result.error or result.failed_page_numbers:
        result.extraction_status = "partial" if has_text else "failed"
    elif result.page_count == 0:
        result.extraction_status = "failed"
        result.error = "PDF contains no pages"
    elif not has_text:
        result.extraction_status = "no_text"
    else:
        result.extraction_status = "success"
    if result.extraction_status == "success":
        result.readiness = "review" if result.quality_issues or result.parser_warnings else "ready"


def validate_pdf(path: Path, input_dir: Path, min_page_chars: int = 80) -> DocumentValidation:
    """Isolate document and page failures so one bad PDF cannot stop the audit."""
    if min_page_chars < 1:
        raise ValueError("min_page_chars must be positive")
    result = DocumentValidation(path.name, path.relative_to(input_dir).as_posix())
    collector = _WarningCollector()
    logger = logging.getLogger("pypdf")
    logger.addHandler(collector)
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            try:
                with path.open("rb") as stream:
                    result.sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
                    stream.seek(0)
                    reader = PdfReader(stream, strict=False)
                    if reader.is_encrypted and not reader.decrypt(""):
                        result.extraction_status = "encrypted"
                        result.error = "Password required; cannot extract without a password"
                    else:
                        result.page_count = len(reader.pages)
                        for index in range(result.page_count):
                            collector.page_number = index + 1
                            try:
                                page = validate_page(reader.pages[index], index + 1, min_page_chars)
                            except Exception as exc:
                                page = PageValidation(index + 1, error=f"{type(exc).__name__}: {exc}")
                            result.pages.append(page)
            except Exception as exc:
                result.error = f"{type(exc).__name__}: {exc}"
            finally:
                result.parser_warnings = list(dict.fromkeys(
                    collector.messages + [f"{item.category.__name__}: {item.message}" for item in captured]
                ))
    finally:
        logger.removeHandler(collector)
    _finalize(result)
    return result


def validate_corpus(input_dir: Path, min_page_chars: int = 80) -> list[DocumentValidation]:
    return [validate_pdf(path, input_dir, min_page_chars) for path in discover_pdfs(input_dir)]


def build_report(
    documents: list[DocumentValidation], input_dir: Path, expected_count: int, min_page_chars: int,
) -> dict:
    statuses = Counter(document.extraction_status for document in documents)
    readiness = Counter(document.readiness for document in documents)
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_directory": input_dir.as_posix(),
        "pypdf_version": pypdf.__version__,
        "method": {
            "extraction": "pypdf.PageObject.extract_text (plain mode, strict=False)",
            "character_count": "len(raw extracted text), including whitespace",
            "empty_page": "successful extraction with no non-whitespace text; errors excluded",
            "sparse_text_threshold": min_page_chars,
            "sparse_text_unit": "non-whitespace characters per non-empty page",
            "ocr_applied": False,
            "limitation": "Heuristics do not verify reading order, tables, image text, or semantic accuracy.",
        },
        "summary": {
            "document_count": len(documents),
            "expected_document_count": expected_count,
            "document_count_matches": len(documents) == expected_count,
            "page_count": sum(document.page_count or 0 for document in documents),
            "documents_with_unknown_page_count": sum(document.page_count is None for document in documents),
            "character_count": sum(document.character_count for document in documents),
            "empty_page_count": sum(document.empty_page_count or 0 for document in documents),
            "failed_page_count": sum(len(document.failed_page_numbers) for document in documents),
            "extraction_status_counts": dict(sorted(statuses.items())),
            "readiness_counts": dict(sorted(readiness.items())),
        },
        "documents": [asdict(document) for document in documents],
    }


def save_reports(report: dict, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "pdf_validation.json"
    csv_path = output_dir / "pdf_validation.csv"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    columns = [
        "filename", "relative_path", "sha256", "page_count", "character_count", "empty_page_count",
        "empty_page_numbers", "failed_page_numbers", "extraction_status", "readiness",
        "quality_issues", "parser_warnings", "error",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for document in report["documents"]:
            row = {key: document[key] for key in columns}
            for key in ("empty_page_numbers", "failed_page_numbers", "quality_issues", "parser_warnings"):
                row[key] = json.dumps(row[key], ensure_ascii=False)
            writer.writerow(row)
    return json_path, csv_path


def format_table(documents: list[DocumentValidation]) -> str:
    lines = [
        "| File | Pages | Characters | Empty | Failed pages | Extraction | Readiness | Quality flags |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for document in documents:
        flags = ", ".join(document.quality_issues) or "-"
        if document.parser_warnings:
            flags += f"; parser_warnings={len(document.parser_warnings)}"
        name = document.relative_path.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {name} | {document.page_count if document.page_count is not None else '?'} "
            f"| {document.character_count} "
            f"| {document.empty_page_count if document.empty_page_count is not None else '?'} "
            f"| {len(document.failed_page_numbers)} | {document.extraction_status} "
            f"| {document.readiness} | {flags} |"
        )
    return "\n".join(lines)


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/corpus/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation"))
    parser.add_argument("--expected-count", type=_positive_int, default=15)
    parser.add_argument("--min-page-chars", type=_positive_int, default=80)
    args = parser.parse_args(argv)
    try:
        documents = validate_corpus(args.input_dir, args.min_page_chars)
        report = build_report(documents, args.input_dir, args.expected_count, args.min_page_chars)
        paths = save_reports(report, args.output_dir)
    except OSError as exc:
        parser.exit(2, f"Validation error: {exc}\n")
    print(format_table(documents))
    print("\nSummary: " + json.dumps(report["summary"], ensure_ascii=False))
    for document in documents:
        if document.error:
            print(f"ERROR {document.relative_path}: {document.error}")
        for page in document.pages:
            if page.error:
                print(f"ERROR {document.relative_path}, page {page.page_number}: {page.error}")
    for path in paths:
        print(f"Report: {path}")
    if not report["summary"]["document_count_matches"]:
        print(f"ERROR: Expected {args.expected_count} PDFs, found {len(documents)}")
        return 2
    return 1 if any(document.readiness == "blocked" for document in documents) else 0


if __name__ == "__main__":
    raise SystemExit(main())
