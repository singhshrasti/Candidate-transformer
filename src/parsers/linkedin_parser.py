"""Parser for a simulated LinkedIn profile-API JSON payload."""

from __future__ import annotations

import json
from pathlib import Path

from src.models.candidate import EducationEntry, ExperienceEntry, RawRecord, SourceType
from src.normalizers.date_normalizer import DateNormalizer
from src.parsers.base_parser import BaseParser
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LinkedInParser(BaseParser):
    """Parses a simulated LinkedIn API JSON profile export.

    Expected shape::

        {
          "name": "...", "headline": "...", "location": "...",
          "profile_url": "...", "skills": [...],
          "positions": [{"company": "...", "title": "...",
                          "start_date": "...", "end_date": "..."}],
          "education": [{"school": "...", "degree": "...", "field": "...",
                          "start_date": "...", "end_date": "..."}]
        }
    """

    def parse(self, path: str | Path) -> RawRecord:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"LinkedIn JSON not found: {path}")

        logger.info("Parsing LinkedIn JSON: %s", path)
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        date_normalizer = DateNormalizer()
        experience = [
            ExperienceEntry(
                company=pos.get("company", "Unknown"),
                title=pos.get("title", "Unknown"),
                start_date=date_normalizer.normalize(pos.get("start_date")),
                end_date=date_normalizer.normalize(pos.get("end_date")),
                description=pos.get("description"),
                source=SourceType.LINKEDIN,
            )
            for pos in data.get("positions", [])
        ]

        education = [
            EducationEntry(
                institution=edu.get("school", "Unknown"),
                degree=edu.get("degree"),
                field_of_study=edu.get("field"),
                start_date=date_normalizer.normalize(edu.get("start_date")),
                end_date=date_normalizer.normalize(edu.get("end_date")),
                source=SourceType.LINKEDIN,
            )
            for edu in data.get("education", [])
        ]

        links = {}
        if data.get("profile_url"):
            links["linkedin"] = data["profile_url"]

        return RawRecord(
            source=SourceType.LINKEDIN,
            full_name=data.get("name"),
            location=data.get("location"),
            links=links,
            headline=data.get("headline"),
            skills=data.get("skills", []),
            experience=experience,
            education=education,
            raw_payload=data,
        )
