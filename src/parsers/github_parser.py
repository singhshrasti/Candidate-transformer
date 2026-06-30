"""Parser for a simulated GitHub profile-API JSON payload."""

from __future__ import annotations

import json
from pathlib import Path

from src.models.candidate import RawRecord, SourceType
from src.parsers.base_parser import BaseParser
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubParser(BaseParser):
    """Parses a simulated GitHub API JSON profile export.

    Expected shape::

        {
          "login": "...", "name": "...", "bio": "...",
          "html_url": "...", "location": "...", "email": "...",
          "languages": ["Python", "Go", ...],
          "repos": [{"name": "...", "language": "...", "topics": [...]}]
        }

    Programming languages and repo topics are folded into ``skills``.
    """

    def parse(self, path: str | Path) -> RawRecord:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"GitHub JSON not found: {path}")

        logger.info("Parsing GitHub JSON: %s", path)
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        skills = set(data.get("languages", []))
        for repo in data.get("repos", []):
            if repo.get("language"):
                skills.add(repo["language"])
            skills.update(repo.get("topics", []))

        links = {}
        if data.get("html_url"):
            links["github"] = data["html_url"]

        emails = [data["email"]] if data.get("email") else []

        return RawRecord(
            source=SourceType.GITHUB,
            full_name=data.get("name"),
            emails=emails,
            location=data.get("location"),
            links=links,
            headline=data.get("bio"),
            skills=sorted(skills),
            raw_payload=data,
        )
