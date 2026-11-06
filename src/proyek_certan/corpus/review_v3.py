"""Only visually verified whitespace corrections; v2 artifacts stay immutable."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader
from proyek_certan.corpus.prepare import clean_text

VERSION = "m3-reviewed-v3"


def join_range(text: str, start: str, end: str) -> tuple[str, int]:
    left = re.findall(rf"(?m)^{re.escape(start)}", text)
    a = text.find(start)
    right = (
        re.findall(rf"(?m)^{re.escape(end)}", text[a + len(start) :]) if a >= 0 else []
    )
    if len(left) != 1 or len(right) != 1:
        raise ValueError(
            f"Reviewed source anchor changed: {start!r} ({len(left)}), {end!r} ({len(right)})"
        )
    a = text.index(start)
    b = text.index(end, a + len(start))
    region = text[a:b]
    joined = " ".join(region.split()) + "\n"
    return text[:a] + joined + text[b:], region.count("\n") - 1


def revise_v3(document_id: str, text: str) -> tuple[str, dict]:
    before = text
    joins = 0
    if document_id == "DOC11":
        ranges = [
            ("This document is authored,", "II. OBJECTIVES"),
            (
                "The goal of UCF IT Incident Management",
                "The Incident Management policy and procedure",
            ),
            (
                "The Incident Management policy and procedure",
                "The scope of this process",
            ),
            ("The scope of this process", "III. DEFINITIONS"),
            ("Incident:", "Service Request:"),
            ("Service Request:", "Service Level Agreement (SLA):"),
            ("Service Level Agreement (SLA):", "Service Level Target (SLT):"),
            ("Service Level Target (SLT):", "Problem:"),
            ("Problem:", "Known Error:"),
            ("Known Error:", "Work Around:"),
            ("Work Around:", "Incident Manager -"),
        ]
        for start, end in ranges:
            text, n = join_range(text, start, end)
            joins += n
    elif document_id == "DOC13":
        pairs = [
            (
                "University Network\nAdministration\n",
                "University Network Administration\n",
            ),
            (
                "Vice Provost for Information\nTechnology & Chief Information\nOfficer\n",
                "Vice Provost for Information Technology & Chief Information Officer\n",
            ),
        ]
        for old, new in pairs:
            if text.count(old) != 1:
                raise ValueError("Reviewed source anchor changed")
            text = text.replace(old, new)
            joins += old.count("\n") - new.count("\n")
        text, n = join_range(
            text, "Oregon State University adopted", "Next scheduled review date:"
        )
        joins += n
    if text.split() != before.split():
        raise ValueError("Whitespace correction changed substantive token sequence")
    return text, dict(
        changed=text != before, line_breaks_joined=joins, source_tokens_identical=True
    )


def page_word_index(path: Path, document_id: str) -> tuple[list[str], list[int]]:
    """Build an exact word-to-PDF-page map after verified page furniture removal."""
    words = []
    pages = []
    for number, page in enumerate(PdfReader(path).pages, 1):
        text = clean_text(page.extract_text() or "")
        if document_id == "DOC11":
            text = re.sub(r"(?m)^\d{1,2}\n", "", text)
        if document_id == "DOC13" and number > 1:
            text = text.replace(
                "University Policy 08-010 University Network Administration\n", "", 1
            )
        tokens = text.split()
        words.extend(tokens)
        pages.extend([number] * len(tokens))
    return words, pages


def exact_page_span(text: str, title: str, index: tuple[list[str], list[int]]) -> dict:
    prefix = f"# {title}\n"
    if text.startswith(prefix):
        text = text[len(prefix) :]
    target = text.split()
    words, pages = index
    matches = [
        i
        for i in range(len(words) - len(target) + 1)
        if words[i : i + len(target)] == target
    ]
    if len(matches) != 1 or not target:
        return {}
    a = matches[0]
    b = a + len(target)
    return dict(
        page_start=pages[a],
        page_end=pages[b - 1],
        source_word_start=a,
        source_word_end_exclusive=b,
        page_alignment="exact_unique_word_sequence_after_page_furniture_removal",
    )
