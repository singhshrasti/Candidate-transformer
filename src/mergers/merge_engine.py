"""Merges a cluster of matched ``RawRecord`` objects into one ``CanonicalCandidate``.

Conflict resolution for scalar fields follows the configured
``source_priority`` order (highest priority source wins). List fields
(emails, phones, skills, links, experience, education) are unioned across
all sources, since recruiters generally want maximum coverage rather than
a single source's view. Provenance is tracked per-field: for scalar
fields it records which single source won; for list fields it records
a comma-separated list of every contributing source.
"""

from __future__ import annotations

import uuid
from typing import Dict, List

from src.models.candidate import CanonicalCandidate, RawRecord
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MergeEngine:
    """Combines a cluster of source records into a single canonical candidate."""

    def __init__(self, source_priority: List[str], source_reliability: Dict[str, float]) -> None:
        """
        Args:
            source_priority: Ordered list of source names, highest priority
                first, used to resolve scalar field conflicts.
            source_reliability: Per-source reliability weight (0-1) used
                for confidence scoring.
        """
        self.source_priority = source_priority
        self.source_reliability = source_reliability

    def merge(self, cluster: List[RawRecord]) -> CanonicalCandidate:
        """Merges one cluster of matched records into a ``CanonicalCandidate``.

        Args:
            cluster: Records believed to refer to the same candidate.

        Returns:
            A fully populated, unvalidated-at-this-point ``CanonicalCandidate``.
        """
        ordered = self._order_by_priority(cluster)
        provenance: Dict[str, str] = {}

        full_name, full_name_src = self._first_present(ordered, "full_name")
        if full_name_src:
            provenance["full_name"] = full_name_src

        location, location_src = self._first_present(ordered, "location")
        if location_src:
            provenance["location"] = location_src

        headline, headline_src = self._first_present(ordered, "headline")
        if headline_src:
            provenance["headline"] = headline_src

        years_experience, years_src = self._first_present(ordered, "years_experience")
        if years_src:
            provenance["years_experience"] = years_src

        emails, emails_srcs = self._union_list(ordered, "emails")
        if emails_srcs:
            provenance["emails"] = ",".join(emails_srcs)

        phones, phones_srcs = self._union_list(ordered, "phones")
        if phones_srcs:
            provenance["phones"] = ",".join(phones_srcs)

        skills, skills_srcs = self._union_list(ordered, "skills")
        if skills_srcs:
            provenance["skills"] = ",".join(skills_srcs)

        links: Dict[str, str] = {}
        link_srcs = set()
        for record in ordered:
            for key, value in record.links.items():
                if key not in links and value:
                    links[key] = value
                    link_srcs.add(record.source.value)
        if link_srcs:
            provenance["links"] = ",".join(sorted(link_srcs))

        experience = []
        experience_srcs = set()
        for record in ordered:
            if record.experience:
                experience.extend(record.experience)
                experience_srcs.add(record.source.value)
        if experience_srcs:
            provenance["experience"] = ",".join(sorted(experience_srcs))

        education = []
        education_srcs = set()
        for record in ordered:
            if record.education:
                education.extend(record.education)
                education_srcs.add(record.source.value)
        if education_srcs:
            provenance["education"] = ",".join(sorted(education_srcs))

        overall_confidence = self._compute_confidence(cluster)

        return CanonicalCandidate(
            candidate_id=str(uuid.uuid4()),
            full_name=full_name,
            emails=emails,
            phones=phones,
            location=location,
            links=links,
            headline=headline,
            years_experience=years_experience,
            skills=skills,
            experience=experience,
            education=education,
            provenance=provenance,
            overall_confidence=overall_confidence,
        )

    def _order_by_priority(self, cluster: List[RawRecord]) -> List[RawRecord]:
        """Sorts cluster records by configured source priority (highest first)."""

        def priority_index(record: RawRecord) -> int:
            try:
                return self.source_priority.index(record.source.value)
            except ValueError:
                return len(self.source_priority)

        return sorted(cluster, key=priority_index)

    @staticmethod
    def _first_present(ordered: List[RawRecord], field: str):
        """Returns the value (and contributing source) from the highest-priority
        record that has a non-empty value for ``field``."""
        for record in ordered:
            value = getattr(record, field)
            if value not in (None, "", []):
                return value, record.source.value
        return None, None

    @staticmethod
    def _union_list(ordered: List[RawRecord], field: str):
        """Unions a list-valued field across all records, preserving priority order
        and de-duplicating, while tracking every contributing source."""
        seen: List = []
        sources: List[str] = []
        for record in ordered:
            values = getattr(record, field)
            if values:
                contributed = False
                for value in values:
                    if value not in seen:
                        seen.append(value)
                        contributed = True
                if contributed:
                    sources.append(record.source.value)
        return seen, sources

    def _compute_confidence(self, cluster: List[RawRecord]) -> float:
        """Computes overall confidence as the average reliability weight of
        every contributing source, weighted by how many fields each source
        actually contributed."""
        weights = []
        for record in cluster:
            reliability = self.source_reliability.get(record.source.value, 0.5)
            field_count = sum(
                1
                for f in ("full_name", "emails", "phones", "location", "headline", "skills")
                if getattr(record, f)
            )
            if field_count > 0:
                weights.extend([reliability] * field_count)

        if not weights:
            return 0.0
        return round(sum(weights) / len(weights), 4)
