"""Audit the five flagged sources without replacing frozen corpus artifacts.

Default checks hashed HTML snapshots and original PDF page boundaries offline.
--refresh also downloads official sources into an ignored, separate directory.
Changed upstream content is reported, never substituted into the study corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from build_reviewed_corpus import sha, write_json
from proyek_certan.corpus.prepare import (
    USER_AGENT,
    SourceUnavailable,
    _get_limited,
    extract_html_text,
    extract_pdf_text,
    robots_allows,
)
from proyek_certan.corpus.revision import revise_text

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"DOC06", "DOC09", "DOC10", "DOC11", "DOC13"}


def run(refresh: bool = False) -> dict:
    corpus = json.loads(
        (ROOT / "evaluation/reviewed_corpus_v2.json").read_text(encoding="utf-8")
    )
    checks = {
        c["document_id"]: c for c in corpus["source_checks"]
    }
    rows = []
    with requests.Session() as session:
        session.headers["User-Agent"] = USER_AGENT
        session.max_redirects = 3
        robots_cache = {}
        for doc in corpus["documents"]:
            doc_id = doc["document_id"]
            if doc_id not in TARGETS:
                continue
            original = (ROOT / doc["text_file"]).read_text(encoding="utf-8")
            raw = ROOT / "data/corpus/raw" / doc["filename"]
            if sha(raw) != doc["source_pdf_sha256"]:
                raise ValueError(f"{doc_id}: original PDF hash changed")
            if sha(ROOT / doc["text_file"]) != doc["original_text_sha256"]:
                raise ValueError(f"{doc_id}: original text hash changed")
            revised, operations = revise_text(doc_id, original)
            if revised != (ROOT / doc["revised_text_file"]).read_text(encoding="utf-8"):
                raise ValueError(f"{doc_id}: revised text changed")
            row = {
                "document_id": doc_id,
                "source_url": doc["source_url"],
                "verified_source_url": doc["verified_source_url"],
                "original_text_sha256": doc["original_text_sha256"],
                "revised_text_sha256": doc["text_sha256"],
                "source_pdf_sha256": sha(raw),
                "operations": operations,
                "review_required": doc["review_required"],
                "unresolved": doc["unresolved"],
            }
            if doc_id in checks:
                cached = ROOT / f".local/corpus-review-v2/{doc_id}.html"
                if sha(cached) != checks[doc_id]["html_sha256"]:
                    raise ValueError(f"{doc_id}: HTML snapshot hash changed")
                # Recompute rather than trusting an earlier boolean in a report.
                equal = extract_html_text(cached.read_bytes(), doc["publisher"]) == original
                if not equal:
                    raise ValueError(f"{doc_id}: HTML snapshot extraction differs")
                row["source_evidence"] = {
                    "format": "official_html_snapshot",
                    "html_sha256": sha(cached),
                    "extraction_equals_original": equal,
                    "snapshot_time_known": "retrieved_at_utc" in checks[doc_id],
                    "scope": "Article body; figures and code presentation require separate interpretation.",
                }
            else:
                reader = PdfReader(raw)
                if extract_pdf_text(raw, doc["title"]) != original:
                    raise ValueError(f"{doc_id}: PDF extraction differs")
                pages = [p.extract_text() or "" for p in reader.pages]
                if doc_id == "DOC11":
                    folios = [re.findall(r"(?m)^\s*(\d{1,2})\s*$", t) for t in pages]
                    if folios != [[str(n)] for n in range(1, 17)]:
                        raise ValueError("DOC11: numeric line is not a verified page folio")
                    anchors = {
                        "document_control": {"page": 1, "present": "No other parties have the authority" in pages[0]},
                        "figure_1_1": {"page": 5, "present": "Figure 1.1" in pages[4]},
                        "sla_workflow": {"page": 6, "present": "Notification workflow" in pages[5]},
                    }
                else:
                    header = "University Policy 08-010 University Network Administration"
                    # The history on page 4 also names the policy twice; only
                    # leading page furniture is eligible for removal.
                    leading_headers = [" ".join(t.split()).startswith(header) for t in pages]
                    if len(pages) != 5 or not all(leading_headers):
                        raise ValueError("DOC13: page/header anchors changed")
                    anchors = {
                        "revision_2024": {"page": 1, "present": "August 6, 2024" in pages[0]},
                        "wifi_clause": {"page": 3, "present": "5.3.1." in pages[2]},
                        "contacts": {"page": 5, "present": "Contacts" in pages[4]},
                    }
                if not all(a["present"] for a in anchors.values()):
                    raise ValueError(f"{doc_id}: source anchor absent")
                row["source_evidence"] = {
                    "format": "original_local_pdf",
                    "pages": len(pages),
                    "extraction_equals_original": True,
                    "page_anchors": anchors,
                    "visual_layout_certified": False,
                }
            if doc_id in {"DOC09", "DOC10"}:
                if "DRAFT" not in revised or "[Diisi" not in revised:
                    raise ValueError(f"{doc_id}: DRAFT or institutional placeholders lost")
                row["draft_and_placeholders_preserved"] = True
            if refresh:
                current = {"checked_at_utc": datetime.now(UTC).isoformat()}
                try:
                    allowed, note = robots_allows(session, doc["source_url"], robots_cache)
                    current["robots"] = note
                    if not allowed:
                        raise ValueError("robots.txt disallows audit")
                    response, body = _get_limited(session, doc["source_url"])
                    extension = "html" if doc_id in checks else "pdf"
                    snapshot = ROOT / f".local/corpus-review-v2-current/{doc_id}.{extension}"
                    snapshot.parent.mkdir(parents=True, exist_ok=True)
                    snapshot.write_bytes(body)
                    current.update(
                        final_url=response.url,
                        content_type=response.headers.get("Content-Type"),
                        downloaded_sha256=hashlib.sha256(body).hexdigest(),
                        snapshot=snapshot.relative_to(ROOT).as_posix(),
                    )
                    if extension == "html":
                        equal = extract_html_text(body, doc["publisher"]) == original
                    else:
                        equal = extract_pdf_text(snapshot, doc["title"]) == original
                        current["pdf_bytes_equal_original"] = sha(snapshot) == sha(raw)
                    current["extraction_equals_original"] = equal
                    current["status"] = "same_text" if equal else "upstream_changed_review_required"
                    if doc_id == "DOC13" and not equal:
                        # The historical manifest URL serves the 2016 PDF.
                        # Resolve the current PDF from the official policy page;
                        # keep the historical URL and study bytes unchanged.
                        landing_url = "https://policy.oregonstate.edu/UPSM/08-010_university_network_administration"
                        allowed, _ = robots_allows(session, landing_url, robots_cache)
                        if not allowed:
                            raise ValueError("robots.txt disallows policy landing page")
                        _, html = _get_limited(session, landing_url)
                        soup = BeautifulSoup(html, "html.parser")
                        links = {
                            urljoin(landing_url, a["href"])
                            for a in soup.select("a[href]")
                            if a.get_text(strip=True) == "(PDF)"
                            and urlparse(urljoin(landing_url, a["href"])).path.lower().endswith(".pdf")
                        }
                        if len(links) != 1:
                            raise ValueError("current official PDF link is ambiguous")
                        verified_url = links.pop()
                        allowed, _ = robots_allows(session, verified_url, robots_cache)
                        if not allowed:
                            raise ValueError("robots.txt disallows current PDF")
                        _, official_pdf = _get_limited(session, verified_url)
                        verified = snapshot.with_name("DOC13-canonical-2024.pdf")
                        verified.write_bytes(official_pdf)
                        current["canonical_provenance"] = {
                            "landing_url": landing_url,
                            "landing_sha256": hashlib.sha256(html).hexdigest(),
                            "verified_source_url": verified_url,
                            "pdf_sha256": sha(verified),
                            "pdf_bytes_equal_original": sha(verified) == sha(raw),
                            "extraction_equals_original": extract_pdf_text(verified, doc["title"]) == original,
                            "note": "Historical URL serves 2016; official landing page links the 2024 revision used by the frozen corpus. Original source_url retained as historical provenance, not a current-version guarantee.",
                        }
                except (requests.RequestException, SourceUnavailable, PyPdfError, ValueError, OSError) as error:
                    current.update(status="unavailable", error=str(error))
                row["current_source"] = current
            rows.append(row)
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "corpus_report_sha256": sha(ROOT / "evaluation/reviewed_corpus_v2.json"),
        "scope": "Five flagged sources, deterministic safe corrections, no source replacement.",
        "visual_limitations": "No full local PDF visual certification: Poppler unavailable and prior PyMuPDF DLL blocked. Text/page-boundary checks do not establish table/diagram reading order.",
        "documents": rows,
    }
    write_json(ROOT / "evaluation/source_review_v2.json", report)
    for row in rows:
        print(row["document_id"], row["operations"], row.get("current_source", {}).get("status", "offline"))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Recheck official URLs without changing study inputs")
    run(parser.parse_args().refresh)
