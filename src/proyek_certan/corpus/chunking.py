"""Recursive structure-aware splitting with word overlap and a token budget."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import re
from collections.abc import Callable

from proyek_certan.knowledge.models import KnowledgeChunk


WORD = re.compile(r"\S+")
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
ROMAN_HEADING = re.compile(r"^[IVX]+\.\s+([A-Z][A-Z0-9 ,/&:()\-]+)\s*$")
NUMBERED_HEADING = re.compile(r"^\d+(?:\.\d+)*\.\s+(.+?)\s*$")


def recursive_boundary(boundaries: list[list[int]], minimum: int, target: int, level: int = 0) -> int:
    """Recursively try paragraph, line, sentence, then whole-word boundaries.

    The caller finds a token-safe window first. A separator must leave at least
    half the window; otherwise the oversized fragment is split at a finer level.
    """
    if level == len(boundaries):
        return target
    candidates = [end for end in boundaries[level] if minimum < end <= target]
    if candidates:
        return candidates[-1]
    return recursive_boundary(boundaries, minimum, target, level + 1)


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


def chunk_section(
    section: Section, size: int = 250, overlap: int = 40,
    *, token_count: Callable[[str], int] | None = None, max_tokens: int | None = None,
) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("require size > 0 and 0 <= overlap < size")
    if (token_count is None) != (max_tokens is None):
        raise ValueError("token_count and max_tokens must be supplied together")
    if max_tokens is not None and max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    words = list(WORD.finditer(section.text))
    if not words:
        return []
    starts = [word.start() for word in words]
    boundaries = [
        sorted({bisect_right(starts, match.start()) for match in re.finditer(pattern, section.text)})
        for pattern in (r"\n\s*\n", r"\n+", r"(?<=[.!?])\s+")
    ]
    chunks = []
    start = previous_end = 0
    while start < len(words):
        target = min(start + size, len(words))
        if token_count is not None and max_tokens is not None:
            # Search word boundaries using the model's full input length,
            # including its special tokens. Never ask the encoder to truncate.
            low, high = start + 1, target
            safe_end = start
            while low <= high:
                middle = (low + high) // 2
                candidate = section.text[words[start].start():words[middle - 1].end()]
                if token_count(candidate) <= max_tokens:
                    safe_end = middle
                    low = middle + 1
                else:
                    high = middle - 1
            if safe_end == start:
                if start < previous_end:
                    start = previous_end
                    continue
                raise ValueError(f"single word exceeds the {max_tokens}-token limit in {section.title!r}")
            if safe_end <= previous_end:
                # A long word after an overlap can leave no room for new text.
                # Drop only the overlap; the preceding chunk already has it.
                start = previous_end
                continue
            target = safe_end
        if target == len(words):
            end = target
        else:
            end = recursive_boundary(
                boundaries, max(previous_end, start + (target - start) // 2), target,
            )
        chunks.append(section.text[words[start].start():words[end - 1].end()])
        if end == len(words):
            break
        previous_end = end
        start = max(start + 1, end - overlap)
    return chunks


def chunk_document(
    text: str, *, document_id: str, source: str, title: str,
    source_url: str, size: int = 250, overlap: int = 40,
    review_required: bool = False, publication_status: str | None = None,
    token_count: Callable[[str], int] | None = None, max_tokens: int | None = None,
) -> list[KnowledgeChunk]:
    chunks = []
    for section in group_short_sections(split_sections(text, title), size):
        for part in chunk_section(
            section, size, overlap, token_count=token_count, max_tokens=max_tokens,
        ):
            index = len(chunks)
            metadata = {
                "document_id": document_id,
                "source": source,
                "title": title,
                "section": section.title,
                "chunk_index": index,
                "source_url": source_url,
                "review_required": review_required,
            }
            if publication_status:
                metadata["publication_status"] = publication_status
            chunks.append(KnowledgeChunk(
                chunk_id=f"{document_id}-{index:04d}",
                text=part,
                metadata=metadata,
            ))
    return chunks
