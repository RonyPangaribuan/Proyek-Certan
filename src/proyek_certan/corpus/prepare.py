"""Prepare a provenance-checked UTF-8 text corpus without OCR or PDF changes.

Run from the repository root:
``uv run --frozen --no-sync python -m proyek_certan.corpus.prepare``.
Only one official HTML page per manifest entry is fetched. A failed fetch stays
manual_required; content is never invented or replaced by search snippets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from pypdf import PdfReader


USER_AGENT = "CERTAN-CorpusAudit/1.0 (academic, one-page-per-document)"
ALLOWED_HOSTS = {
    "learn.microsoft.com", "docs.dtsi.uhb.ac.id",
    "regulations.utah.edu", "wmich.edu", "cispo.college.indiana.edu",
    "it.ucf.edu", "policy.oregonstate.edu", "docs.openvswitch.org",
}
MAX_HTML_BYTES = 2_000_000
MIN_TEXT_CHARACTERS = 300
MICROSOFT_LICENSE_URL = "https://github.com/MicrosoftDocs/SupportArticles-docs/blob/main/LICENSE"


class SourceUnavailable(Exception):
    """A source cannot be fetched or verified without manual action."""


def _origin(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise SourceUnavailable(f"URL sumber bukan HTTPS pada host resmi yang disetujui: {url}")
    return f"https://{parsed.netloc}"


def _get_limited(session: requests.Session, url: str) -> tuple[requests.Response, bytes]:
    _origin(url)
    response = session.get(url, timeout=(5, 20), stream=True)
    try:
        _origin(response.url)
        response.raise_for_status()
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_HTML_BYTES:
            raise SourceUnavailable(f"Respons lebih besar dari {MAX_HTML_BYTES} byte")
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=65536):
            total += len(chunk)
            if total > MAX_HTML_BYTES:
                raise SourceUnavailable(f"Respons lebih besar dari {MAX_HTML_BYTES} byte")
            chunks.append(chunk)
        return response, b"".join(chunks)
    finally:
        response.close()


def robots_allows(
    session: requests.Session, url: str, cache: dict[str, tuple[RobotFileParser | None, str]],
) -> tuple[bool, str]:
    origin = _origin(url)
    if origin not in cache:
        robots_url = origin + "/robots.txt"
        try:
            response, content = _get_limited(session, robots_url)
            parser = RobotFileParser()
            parser.parse(content.decode(response.encoding or "utf-8", errors="replace").splitlines())
            cache[origin] = (parser, "robots.txt tersedia")
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                cache[origin] = (None, "robots.txt tidak tersedia (HTTP 404)")
            else:
                raise SourceUnavailable(f"robots.txt tidak dapat diperiksa: {exc}") from exc
        except requests.RequestException as exc:
            raise SourceUnavailable(f"robots.txt tidak dapat diperiksa: {exc}") from exc
    parser, note = cache[origin]
    return (parser.can_fetch(USER_AGENT, url) if parser is not None else True), note


def _inline(tag: Tag) -> str:
    return re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()


def _render_list(tag: Tag, lines: list[str], depth: int = 0) -> None:
    for index, item in enumerate(tag.find_all("li", recursive=False), start=1):
        prefix = f"{index}." if tag.name == "ol" else "-"
        plain_parts = []
        nested = []
        for child in item.children:
            if isinstance(child, Comment):
                continue
            if isinstance(child, NavigableString):
                plain_parts.append(str(child))
            elif isinstance(child, Tag) and child.name in {"ul", "ol"}:
                nested.append(child)
            elif isinstance(child, Tag):
                plain_parts.append(_inline(child))
        content = re.sub(r"\s+", " ", " ".join(plain_parts)).strip()
        if content:
            lines.append(f"{'  ' * depth}{prefix} {content}")
        for sublist in nested:
            _render_list(sublist, lines, depth + 1)


def _render(node: Tag, lines: list[str]) -> None:
    for child in node.children:
        if not isinstance(child, Tag):
            if isinstance(child, NavigableString) and not isinstance(child, Comment) and str(child).strip():
                lines.append(re.sub(r"\s+", " ", str(child)).strip())
            continue
        name = child.name
        if name in {"script", "style", "nav", "footer", "aside", "button", "form", "svg", "noscript"}:
            continue
        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            value = _inline(child)
            if value:
                lines.append(f"{'#' * int(name[1])} {value}")
        elif name in {"p", "dt", "dd"}:
            value = _inline(child)
            if value:
                lines.append(value)
        elif name in {"ul", "ol"}:
            _render_list(child, lines)
        elif name == "pre":
            value = child.get_text("\n", strip=True)
            if value:
                lines.append(value)
        elif name == "table":
            for row in child.find_all("tr"):
                cells = [_inline(cell) for cell in row.find_all(["th", "td"], recursive=False)]
                if cells:
                    lines.append(" | ".join(cells))
        elif name == "img":
            alt = child.get("alt", "").strip()
            if alt and not alt.lower().startswith(("icon", "logo")):
                lines.append(f"[Gambar: {alt}]")
        else:
            _render(child, lines)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    for invisible in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        text = text.replace(invisible, "")
    text = re.sub(r"\bPage \d+ of \d+\b", "", text)
    lines = []
    for original in text.splitlines():
        stripped = original.strip()
        if not stripped:
            continue
        line = re.sub(r"[ \t]+", " ", stripped)
        if re.match(r"^(?:-|\d+\.) ", line):
            indentation = len(original) - len(original.lstrip())
            if indentation:
                line = "  " * max(1, indentation // 2) + line
        lines.append(line)
    return "\n".join(lines) + "\n"


def extract_html_text(html: bytes, publisher: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if publisher == "Microsoft Learn":
        candidates = soup.select("main .content")
        root = max(candidates, key=lambda element: len(_inline(element)), default=None)
        heading = soup.find("h1")
    elif publisher == "DTSI Universitas Harapan Bangsa":
        root = soup.select_one("main article.md-content__inner")
        heading = None
    elif publisher == "The University of Utah":
        root = soup.select_one("main section.uu-section")
        heading = None
    elif publisher == "Open vSwitch Project":
        root = soup.select_one("main#content section#vlans")
        heading = None
    else:
        root = soup.select_one("main article") or soup.select_one("main")
        heading = None
    if root is None:
        raise SourceUnavailable("Elemen isi utama HTML tidak ditemukan")
    for unwanted in root.select(
        "nav, footer, aside, script, style, form, button, .breadcrumb, .breadcrumbs, "
        "[class*='cookie'], [id*='cookie'], [class*='feedback'], [id*='feedback'], "
        "[class*='sidebar'], [class*='navigation'], [class*='table-of-contents'], "
        "a.headerlink"
    ):
        unwanted.decompose()
    lines = []
    if heading is not None and heading not in root.descendants:
        lines.append("# " + _inline(heading))
    _render(root, lines)
    lines = [line for line in lines if not (
        line.startswith("Try our Virtual Agent -")
        or line.strip() in {"### View PDF", "## View PDF", "View PDF"}
        or line.startswith("Register SOP:")
    )]
    text = clean_text("\n".join(lines))
    if len(text.strip()) < MIN_TEXT_CHARACTERS:
        raise SourceUnavailable(f"Konten utama terlalu pendek ({len(text.strip())} karakter)")
    if not re.search(r"(?m)^#{1,6} ", text):
        raise SourceUnavailable("Heading dokumen tidak ditemukan pada hasil ekstraksi")
    if re.search(r"(?i)(verify you are human|enable javascript to continue|access denied)", text[:500]):
        raise SourceUnavailable("Halaman akses/challenge, bukan isi artikel")
    return text


def extract_pdf_text(path: Path, title: str) -> str:
    reader = PdfReader(path, strict=False)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            raise SourceUnavailable(f"Halaman {number} PDF tidak menghasilkan teks")
        pages.append(clean_text(text).strip())
    return f"# {title}\n\n" + "\n\n".join(pages) + "\n"


def _sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _previous_results(root: Path) -> dict[str, dict]:
    path = root / "evaluation/corpus_processing.json"
    if not path.is_file():
        return {}
    report = json.loads(path.read_text(encoding="utf-8"))
    return {item["document_id"]: item for item in report["documents"]}


def _reusable_text(previous: dict | None, document: dict, pdf_hash: str, outfile: Path) -> str | None:
    """Reuse only a verified output from the same source and identical raw PDF."""
    if not previous or previous.get("status") != "processed":
        return None
    if previous.get("source_url") != document["source_url"]:
        return None
    if previous.get("source_pdf_sha256") != pdf_hash:
        return None
    if previous.get("text_file") != f"data/corpus/processed/{outfile.name}":
        return None
    if not outfile.is_file() or _sha256(outfile) != previous.get("sha256"):
        return None
    try:
        text = outfile.read_text(encoding="utf-8")
    except UnicodeError:
        return None
    if len(text) != previous.get("character_count") or len(text.strip()) < MIN_TEXT_CHARACTERS:
        return None
    return text


def process_corpus(root: Path, session: requests.Session | None = None) -> dict:
    manifest_path = root / "data/corpus/corpus_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validation = json.loads((root / "evaluation/pdf_validation.json").read_text(encoding="utf-8"))
    expected = {item["filename"]: item for item in validation["documents"]}
    previous_results = _previous_results(root)
    documents = manifest["documents"]
    if len(documents) != len(expected) or {item["filename"] for item in documents} != set(expected):
        raise ValueError("Manifest dan laporan validasi harus memuat 15 PDF yang sama")
    if len({item["document_id"] for item in documents}) != len(documents):
        raise ValueError("document_id dalam manifest harus unik")
    owned = session is None
    session = session or requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    session.max_redirects = 3
    robots_cache: dict = {}
    results = []
    output_dir = root / "data/corpus/processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        for document in documents:
            filename = document["filename"]
            pdf = root / "data/corpus/raw" / filename
            outfile = output_dir / (Path(filename).stem + ".txt")
            entry = {
                "document_id": document["document_id"], "filename": filename,
                "source_url": document["source_url"], "method": None,
                "status": "manual_required", "text_file": None,
                "character_count": 0, "word_count": 0, "heading_count": 0,
                "list_item_count": 0, "sha256": None, "reason": None,
                "source_pdf_sha256": None, "reused_existing": False,
            }
            try:
                if not pdf.is_file() or _sha256(pdf) != expected[filename]["sha256"]:
                    raise SourceUnavailable("PDF asli hilang atau SHA-256 berbeda dari laporan validasi")
                entry["source_pdf_sha256"] = expected[filename]["sha256"]
                if document.get("automatic_extraction_allowed") is False:
                    reason = document.get("manual_reason", "Ekstraksi otomatis tidak diizinkan")
                    raise SourceUnavailable(reason.removeprefix("SourceUnavailable: "))
                previous = previous_results.get(document["document_id"])
                reused = _reusable_text(previous, document, entry["source_pdf_sha256"], outfile)
                if reused is not None:
                    text = reused
                    method = previous["method"]
                    entry.update({key: value for key, value in previous.items() if key not in entry})
                    entry["reused_existing"] = True
                elif expected[filename]["extraction_status"] == "success":
                    text = extract_pdf_text(pdf, document["title"])
                    method = "pypdf"
                elif expected[filename]["extraction_status"] == "no_text":
                    url = document["source_url"]
                    allowed, robots_note = robots_allows(session, url, robots_cache)
                    if not allowed:
                        raise SourceUnavailable(f"robots.txt melarang URL: {url}")
                    response, body = _get_limited(session, url)
                    if response.url != url:
                        raise SourceUnavailable(f"URL final berbeda dari URL yang diperiksa: {response.url}")
                    if "text/html" not in response.headers.get("Content-Type", "").lower():
                        raise SourceUnavailable("Sumber tidak mengembalikan HTML")
                    text = extract_html_text(body, document["publisher"])
                    method = "official_html"
                    entry["robots_note"] = robots_note
                    entry["final_url"] = response.url
                    if document["publisher"] == "Microsoft Learn":
                        entry["license_url"] = MICROSOFT_LICENSE_URL
                        entry["transformation"] = "HTML article body to cleaned UTF-8 plain text"
                        document["license_url"] = MICROSOFT_LICENSE_URL
                        document["transformation"] = entry["transformation"]
                else:
                    raise SourceUnavailable("Status PDF awal tidak didukung untuk ekstraksi otomatis")
                if not entry["reused_existing"]:
                    outfile.write_text(text, encoding="utf-8", newline="\n")
                entry.update({
                    "method": method, "status": "processed", "text_file": outfile.relative_to(root).as_posix(),
                    "character_count": len(text), "word_count": len(text.split()),
                    "heading_count": sum(bool(re.match(r"^#{1,6} ", line)) for line in text.splitlines()),
                    "list_item_count": sum(bool(re.match(r"^\s*(?:-|\d+\.) ", line)) for line in text.splitlines()),
                    "sha256": _sha256(outfile),
                    "quality_flags": ["replacement_characters"] if "\ufffd" in text else [],
                })
                if document.get("publication_status", "").startswith("DRAFT"):
                    entry["quality_flags"].append("draft_source")
                document["source_status"] = "processed_pdf" if method == "pypdf" else "processed_official_html"
                document["text_file"] = entry["text_file"]
                document.pop("manual_reason", None)
            except (SourceUnavailable, requests.RequestException, OSError, ValueError) as exc:
                entry["reason"] = f"{type(exc).__name__}: {exc}"
                document["source_status"] = "manual_required"
                document["manual_reason"] = str(exc)
                document.pop("text_file", None)
            results.append(entry)
            print(f"{entry['document_id']}: {entry['status']} ({entry['character_count']} chars)", flush=True)
    finally:
        if owned:
            session.close()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "One official HTML page per no_text document; pypdf for extractable PDFs; verified existing outputs reused; no OCR",
        "summary": {
            "document_count": len(results),
            "processed_count": sum(item["status"] == "processed" for item in results),
            "manual_required_count": sum(item["status"] == "manual_required" for item in results),
        },
        "documents": results,
    }
    evaluation = root / "evaluation"
    (evaluation / "corpus_processing.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    report = process_corpus(args.root)
    print(json.dumps(report["summary"], ensure_ascii=False))
    for item in report["documents"]:
        if item["reason"]:
            print(f"MANUAL {item['document_id']}: {item['reason']}")
    return 1 if report["summary"]["manual_required_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
