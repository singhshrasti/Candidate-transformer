"""Skill-name normalization: casing, aliasing, and de-duplication."""

from __future__ import annotations

from typing import List

# Maps common variants/aliases to a single canonical skill name.
_SKILL_ALIASES = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "python": "Python",
    "golang": "Go",
    "go": "Go",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "aws": "AWS",
    "gcp": "GCP",
    "ci/cd": "CI/CD",
    "rest apis": "REST APIs",
    "restapi": "REST APIs",
}


class SkillNormalizer:
    """Normalizes raw skill strings into a canonical, de-duplicated set."""

    def normalize(self, raw: str) -> str:
        """Normalizes a single skill name.

        Applies whitespace trimming, alias resolution, and falls back to
        title-casing for unrecognized terms.
        """
        cleaned = " ".join(raw.strip().split())
        key = cleaned.lower()
        if key in _SKILL_ALIASES:
            return _SKILL_ALIASES[key]
        return cleaned if cleaned.isupper() else cleaned.title()

    def normalize_many(self, raws: List[str]) -> List[str]:
        """Normalizes and de-duplicates a list of skill names, preserving order."""
        seen = []
        for raw in raws:
            if not raw or not raw.strip():
                continue
            normalized = self.normalize(raw)
            if normalized not in seen:
                seen.append(normalized)
        return seen
