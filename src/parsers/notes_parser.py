"""Parser for free-form Recruiter Notes (.txt) files.

Recruiter notes are the least structured and least reliable source in the
pipeline. This parser extracts whatever contact info and skill keywords it
can find via simple regex/keyword matching, mirroring the resume parser's
approach but with lower expectations of completeness.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.models.candidate import RawRecord, SourceType
from src.parsers.base_parser import BaseParser
from src.parsers.resume_parser import _EMAIL_RE, _KNOWN_SKILLS, _PHONE_RE
from src.utils.logger import get_logger

logger = get_logger(__name__)

_NAME_LINE_RE = re.compile(r"(?:candidate|name)\s*[:\-]\s*(.+)", re.IGNORECASE)


class RecruiterNotesParser(BaseParser):
    """Parses unstructured free-text recruiter notes."""

    def parse(self, path: str | Path) -> RawRecord:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Recruiter notes not found: {path}")

        logger.info("Parsing recruiter notes: %s", path)
        text = path.read_text(encoding="utf-8")

        name_match = _NAME_LINE_RE.search(text)
        full_name = name_match.group(1).strip() if name_match else None

        emails = list(dict.fromkeys(_EMAIL_RE.findall(text)))
        phones = list(dict.fromkeys(m.strip() for m in _PHONE_RE.findall(text)))

        lowered = text.lower()
        skills = sorted({skill.title() for skill in _KNOWN_SKILLS if skill in lowered})

        return RawRecord(
            source=SourceType.NOTES,
            full_name=full_name,
            emails=emails,
            phones=phones,
            skills=skills,
            raw_payload={"raw_text": text},
        )
