"""Offline checks for token-aware section and word chunking."""

from __future__ import annotations

from proyek_certan.corpus.chunking import Section, chunk_document, chunk_section
from proyek_certan.corpus.ingestion import verify_coverage


def count_with_specials(text: str) -> int:
    return 2 + sum(2 if word.startswith("long") else 1 for word in text.split())


def test_token_cap_overlap_and_complete_word_order():
    text = "# Guide\n" + " ".join(f"long{i}" if i % 3 == 0 else f"w{i}" for i in range(75))
    chunks = chunk_document(
        text, document_id="DOC98", source="DOC98.pdf", title="Guide",
        source_url="https://example.org/guide", size=50, overlap=4,
        token_count=count_with_specials, max_tokens=22,
    )
    assert len(chunks) > 1
    assert all(count_with_specials(chunk.text) <= 22 for chunk in chunks)
    assert all(chunks[i - 1].text.split()[-4:] == chunks[i].text.split()[:4]
               for i in range(1, len(chunks)))
    rebuilt = chunks[0].text.split()
    for chunk in chunks[1:]:
        rebuilt.extend(chunk.text.split()[4:])
    assert rebuilt == text.split()
    verify_coverage(text, chunks, 50, 4, count_with_specials, 22)


def test_short_document_metadata_and_determinism():
    kwargs = dict(document_id="DOC09", source="DOC09.pdf", title="Draft guide",
                  source_url="https://example.org/draft", size=30, overlap=3,
                  token_count=count_with_specials, max_tokens=20,
                  review_required=True, publication_status="DRAFT")
    first = chunk_document("# Draft guide\nCheck VLAN.", **kwargs)
    assert first == chunk_document("# Draft guide\nCheck VLAN.", **kwargs)
    assert len(first) == 1
    assert first[0].chunk_id == "DOC09-0000"
    assert first[0].metadata["section"] == "Draft guide"
    assert first[0].metadata["source_url"] == "https://example.org/draft"
    assert first[0].metadata["publication_status"] == "DRAFT"
    assert first[0].metadata["review_required"] is True


def test_section_boundaries_and_progress_when_overlap_is_too_large():
    text = "# One\n" + " ".join(f"a{i}" for i in range(12)) + "\n## Two\n" + " ".join(f"b{i}" for i in range(12))
    chunks = chunk_document(text, document_id="DOC01", source="DOC01.pdf", title="Guide",
                            source_url="https://example.org", size=10, overlap=8,
                            token_count=count_with_specials, max_tokens=9)
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
    assert all(count_with_specials(chunk.text) <= 9 for chunk in chunks)
    assert [chunk.metadata["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    assert any(chunk.metadata["section"] == "Two" for chunk in chunks)
    verify_coverage(text, chunks, 10, 8, count_with_specials, 9)


def test_oversized_single_word_fails_explicitly():
    import pytest

    with pytest.raises(ValueError, match="single word exceeds"):
        chunk_section(Section("test", "unbroken"), size=20, overlap=2,
                      token_count=lambda _: 30, max_tokens=12)
