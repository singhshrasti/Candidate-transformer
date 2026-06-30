"""Parser for the structured ATS (Applicant Tracking System) JSON blob."""

from __future__ import annotations

import json
from pathlib import Path

from src.models.candidate import EducationEntry, ExperienceEntry, RawRecord, SourceType
from src.parsers.base_parser import BaseParser
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ATSJSONParser(BaseParser):
    """Parses an ATS export JSON blob into a ``RawRecord``.

    Expected shape (extra/missing keys are tolerated)::

        {
          "candidate": {
            "name": "...", "emails": [...], "phones": [...],
            "location": "...", "headline": "...",
            "skills": [...], "years_experience": 5.5,
            "experience": [{"company": "...", "title": "...",
                             "start_date": "...", "end_date": "..."}],
            "education": [{"institution": "...", "degree": "...",
                            "field_of_study": "...", "start_date": "...", "end_date": "..."}],
            "links": {"linkedin": "...", "github": "..."}
          }
        }
    """

    def parse(self, path: str | Path) -> RawRecord:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"ATS JSON not found: {path}")

        logger.info("Parsing ATS JSON: %s", path)
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        candidate = data.get("candidate", data)

        experience = [
            ExperienceEntry(
                company=exp.get("company", "Unknown"),
                title=exp.get("title", "Unknown"),
                start_date=exp.get("start_date"),
                end_date=exp.get("end_date"),
                description=exp.get("description"),
                source=SourceType.ATS,
            )
            for exp in candidate.get("experience", [])
        ]

        education = [
            EducationEntry(
                institution=edu.get("institution", "Unknown"),
                degree=edu.get("degree"),
                field_of_study=edu.get("field_of_study"),
                start_date=edu.get("start_date"),
                end_date=edu.get("end_date"),
                source=SourceType.ATS,
            )
            for edu in candidate.get("education", [])
        ]

        return RawRecord(
            source=SourceType.ATS,
            full_name=candidate.get("name"),
            emails=candidate.get("emails", []),
            phones=candidate.get("phones", []),
            location=candidate.get("location"),
            links=candidate.get("links", {}),
            headline=candidate.get("headline"),
            years_experience=candidate.get("years_experience"),
            skills=candidate.get("skills", []),
            experience=experience,
            education=education,
            raw_payload=candidate,
        )
