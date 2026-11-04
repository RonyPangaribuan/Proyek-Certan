"""Section-first, word-aware corpus chunking with deterministic overlap."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import re

from proyek_certan.knowledge.models import KnowledgeChunk


WORD = re.compile(r"\S+")
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
ROMAN_HEADING = re.compile(r"^[IVX]+\.\s+([A-Z][A-Z0-9 ,/&:()\-]+)\s*$")
NUMBERED_HEADING = re.compile(r"^\d+(?:\.\d+)*\.\s+(.+?)\s*$")


@dataclass(frozen=True)
class Section:
    title: str
    text: str


def heading_title(line: str) -> str | None:
    if match := MARKDOWN_HEADING.match(line):
        return match.group(1)
    if line.startswith("Q: "):
        return line[3:].strip()
    if ROMAN_HEADING.match(line):
        return line.strip()
    if match := NUMBERED_HEADING.match(line):
        # Procedure steps end in full stops; keep them inside their parent section.
        if not line.rstrip().endswith(".") and len(line) <= 90 and len(match.group(1).split()) <= 10:
            return line.strip()
    return None


def split_sections(text: str, default_title: str) -> list[Section]:
    sections: list[Section] = []
    lines: list[str] = []
    title = default_title
    for line in text.splitlines(keepends=True):
        found = heading_title(line.rstrip("\n"))
        if found and lines:
            sections.append(Section(title, "".join(lines).strip("\n")))
            lines = []
        if found:
            title = found
        lines.append(line)
    if lines:
        sections.append(Section(title, "".join(lines).strip("\n")))
    return [section for section in sections if section.text.strip()]


def group_short_sections(sections: list[Section], size: int) -> list[Section]:
    """Pack adjacent short sections while retaining each heading in the text."""
    groups = []
    pending: list[Section] = []
    count = 0

    def flush() -> None:
        nonlocal count
        if pending:
            title = " / ".join(section.title for section in pending)
            groups.append(Section(title, "\n".join(section.text for section in pending)))
            pending.clear()
            count = 0

    for section in sections:
        words = len(section.text.split())
        if pending and count + words > size and count > min(40, size // 4):
            flush()
        pending.append(section)
        count += words
        if count >= size // 2:
            flush()
    flush()
    return groups


def chunk_section(section: Section, size: int = 250, overlap: int = 40) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("require size > 0 and 0 <= overlap < size")
    words = list(WORD.finditer(section.text))
    if not words:
        return []
    starts = [word.start() for word in words]
    boundaries = sorted({
        bisect_right(starts, match.start())
        for match in re.finditer(r"\n+", section.text)
    })
    chunks = []
    start = previous_end = 0
    while start < len(words):
        target = min(start + size, len(words))
        if target == len(words):
            end = target
        else:
            preferred = [
                boundary for boundary in boundaries
                if max(previous_end, start + size // 2) < boundary <= target
            ]
            end = preferred[-1] if preferred else target
        chunks.append(section.text[words[start].start():words[end - 1].end()])
        if end == len(words):
            break
        previous_end = end
        start = end - overlap
    return chunks


def chunk_document(
    text: str, *, document_id: str, source: str, title: str,
    source_url: str, size: int = 250, overlap: int = 40,
) -> list[KnowledgeChunk]:
    chunks = []
    for section in group_short_sections(split_sections(text, title), size):
        for part in chunk_section(section, size, overlap):
            index = len(chunks)
            chunks.append(KnowledgeChunk(
                chunk_id=f"{document_id}-{index:04d}",
                text=part,
                metadata={
                    "document_id": document_id,
                    "source": source,
                    "title": title,
                    "section": section.title,
                    "chunk_index": index,
                    "source_url": source_url,
                },
            ))
    return chunks
