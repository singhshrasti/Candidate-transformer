"""Parser for unstructured Resume PDF files.

Uses PyMuPDF (``fitz``) to extract raw text, then applies lightweight
regex/heuristic extraction to pull out structured fields. Resume parsing
is inherently fuzzy; this parser favors precision over recall and leaves
fields ``None``/empty when it cannot confidently extract them.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz  # PyMuPDF

from src.models.candidate import RawRecord, SourceType
from src.parsers.base_parser import BaseParser
from src.utils.logger import get_logger

logger = get_logger(__name__)

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(\+?\d[\d\-\.\s\(\)]{8,}\d)")
_LINKEDIN_RE = re.compile(r"(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+", re.IGNORECASE)
_GITHUB_RE = re.compile(r"(https?://)?(www\.)?github\.com/[A-Za-z0-9\-_/]+", re.IGNORECASE)

_SKILL_SECTION_HEADERS = ("skills", "technical skills", "core competencies")
_KNOWN_SKILLS = [
    "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#",
    "sql", "nosql", "react", "node.js", "django", "flask", "fastapi",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
    "pandas", "numpy", "pytorch", "tensorflow", "machine learning",
    "data engineering", "etl", "spark", "airflow", "kafka", "postgresql",
    "mongodb", "redis", "graphql", "rest apis", "ci/cd", "git",
]


class ResumePDFParser(BaseParser):
    """Extracts candidate fields from a resume PDF via text heuristics."""

    def parse(self, path: str | Path) -> RawRecord:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Resume PDF not found: {path}")

        logger.info("Parsing resume PDF: %s", path)
        text = self._extract_text(path)

        full_name = self._extract_name(text)
        emails = list(dict.fromkeys(_EMAIL_RE.findall(text)))
        phones = list(dict.fromkeys(m.strip() for m in _PHONE_RE.findall(text)))
        linkedin_match = _LINKEDIN_RE.search(text)
        github_match = _GITHUB_RE.search(text)

        links = {}
        if linkedin_match:
            links["linkedin"] = self._normalize_url(linkedin_match.group(0))
        if github_match:
            links["github"] = self._normalize_url(github_match.group(0))

        skills = self._extract_skills(text)
        years_experience = self._estimate_years_experience(text)

        return RawRecord(
            source=SourceType.RESUME,
            full_name=full_name,
            emails=emails,
            phones=phones,
            links=links,
            skills=skills,
            years_experience=years_experience,
            raw_payload={"raw_text": text[:5000]},
        )

    @staticmethod
    def _extract_text(path: Path) -> str:
        """Extracts plain text from every page of the PDF."""
        text_parts = []
        with fitz.open(path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)

    @staticmethod
    def _extract_name(text: str) -> str | None:
        """Heuristically assumes the first non-empty line is the candidate's name."""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and len(stripped.split()) <= 5 and not _EMAIL_RE.search(stripped):
                return stripped
        return None

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url.startswith("http"):
            url = "https://" + url
        return url.rstrip("/.,;")

    @staticmethod
    def _extract_skills(text: str) -> list[str]:
        """Matches known skill keywords against the lowercased resume text."""
        lowered = text.lower()
        found = [skill for skill in _KNOWN_SKILLS if skill in lowered]
        return sorted(set(s.title() if s.islower() else s for s in found))

    @staticmethod
    def _estimate_years_experience(text: str) -> float | None:
        """Looks for an explicit 'N years of experience' style phrase."""
        match = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?\s+(of\s+)?experience", text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None
