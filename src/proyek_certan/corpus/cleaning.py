"""Conservative text normalization for already extracted corpus documents."""

from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize encoding/spacing without changing words, steps, or line order."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    text = text.replace("\u00a0", " ").replace("\ufeff", "")
    text = re.sub(r"[\u200b\u200c\u200d]", "", text)
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    normalized = "\n".join(lines).strip("\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized + "\n" if normalized else ""
