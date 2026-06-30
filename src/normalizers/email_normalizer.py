"""Email-address and generic whitespace normalization."""

from __future__ import annotations

import re
from typing import List, Optional

_EMAIL_VALIDATION_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class EmailNormalizer:
    """Normalizes and validates email address strings."""

    def normalize(self, raw: str) -> Optional[str]:
        """Lowercases and trims an email address, returning ``None`` if invalid."""
        if not raw:
            return None
        cleaned = raw.strip().lower()
        if not _EMAIL_VALIDATION_RE.match(cleaned):
            return None
        return cleaned

    def normalize_many(self, raws: List[str]) -> List[str]:
        """Normalizes and de-duplicates a list of email addresses, preserving order."""
        seen = []
        for raw in raws:
            normalized = self.normalize(raw)
            if normalized and normalized not in seen:
                seen.append(normalized)
        return seen


def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    """Collapses repeated whitespace and trims a string.

    Returns ``None`` if input is ``None`` or becomes empty after trimming.
    """
    if text is None:
        return None
    collapsed = " ".join(text.split())
    return collapsed or None
