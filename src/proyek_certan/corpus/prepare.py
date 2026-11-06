"""Extract a local PDF/HTML/TXT into a new review candidate, without overwrites."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from pypdf import PdfReader
MIN_TEXT_CHARACTERS = 300
class SourceUnavailable(ValueError):
    """Source cannot be extracted reliably without manual review."""

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


def pdf_word_pages(path: Path, document_id: str):
    """Exact page map using the two page-furniture patterns reviewed in the archive."""
    words, pages = [], []
    for number, page in enumerate(PdfReader(path).pages, 1):
        text = clean_text(page.extract_text() or "")
        if document_id == "DOC11":
            text = re.sub(r"(?m)^\d{1,2}\n", "", text)
        if document_id == "DOC13" and number > 1:
            text = text.replace("University Policy 08-010 University Network Administration\n", "", 1)
        tokens = text.split()
        words.extend(tokens)
        pages.extend([number] * len(tokens))
    return words, pages


def exact_page_span(text, title, index):
    """Attach page numbers only for a unique exact word match, never an estimate."""
    prefix = f"# {title}\n"
    if text.startswith(prefix):
        text = text[len(prefix):]
    target = text.split()
    words, pages = index
    matches = [i for i in range(len(words) - len(target) + 1)
               if words[i:i + len(target)] == target]
    if len(matches) != 1 or not target:
        return {}
    first = matches[0]
    return dict(page_start=pages[first], page_end=pages[first + len(target) - 1],
                source_word_start=first, source_word_end_exclusive=first + len(target),
                page_alignment="exact_unique_word_sequence_after_page_furniture_removal")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--kind", choices=("pdf", "html", "text"), required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--publisher", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.kind == "pdf":
            text = extract_pdf_text(args.input, args.title)
        elif args.kind == "html":
            text = extract_html_text(args.input.read_bytes(), args.publisher)
        else:
            text = clean_text(args.input.read_text(encoding="utf-8"))
        if not text.strip():
            raise SourceUnavailable("Extracted text is empty")
        with args.output.open("x", encoding="utf-8", newline="\n") as output:
            output.write(text)
        print("Review candidate written; inspect before registering in the final manifest:", args.output)
        return 0
    except (OSError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")

if __name__ == "__main__":
    raise SystemExit(main())
