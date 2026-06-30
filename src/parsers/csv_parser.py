"""Parser for the structured Recruiter CSV source."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.models.candidate import RawRecord, SourceType
from src.parsers.base_parser import BaseParser
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RecruiterCSVParser(BaseParser):
    """Parses a single-row (per candidate) recruiter CSV export.

    Expected columns (case-insensitive, extra columns are ignored):
    ``name, email, phone, location, headline, skills, linkedin_url, github_url``
    """

    def parse(self, path: str | Path) -> RawRecord:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Recruiter CSV not found: {path}")

        logger.info("Parsing recruiter CSV: %s", path)
        df = pd.read_csv(path)
        if df.empty:
            raise ValueError(f"Recruiter CSV is empty: {path}")

        row = df.iloc[0].to_dict()
        row = {str(k).strip().lower(): v for k, v in row.items()}

        def _get(key: str) -> str | None:
            val = row.get(key)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            return str(val).strip()

        emails = [e.strip() for e in str(_get("email") or "").split(";") if e.strip()]
        phones = [p.strip() for p in str(_get("phone") or "").split(";") if p.strip()]
        skills = [s.strip() for s in str(_get("skills") or "").split(",") if s.strip()]

        links = {}
        if _get("linkedin_url"):
            links["linkedin"] = _get("linkedin_url")
        if _get("github_url"):
            links["github"] = _get("github_url")

        return RawRecord(
            source=SourceType.CSV,
            full_name=_get("name"),
            emails=emails,
            phones=phones,
            location=_get("location"),
            links=links,
            headline=_get("headline"),
            skills=skills,
            raw_payload=row,
        )
