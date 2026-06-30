"""Groups ``RawRecord`` instances that refer to the same candidate.

Matching is attempted, in order, via:
    1. Shared normalized email address
    2. Shared normalized (E.164) phone number
    3. Shared LinkedIn profile URL
    4. Shared GitHub profile URL
    5. Fuzzy full-name similarity (RapidFuzz), above a configurable threshold

Since this is a single-pipeline-run tool (not a database de-dup job), all
input records are assumed to belong to candidates supplied in one batch;
the matcher's job is simply to cluster records that came from different
sources but describe the same person.
"""

from __future__ import annotations

from typing import List

from rapidfuzz import fuzz

from src.models.candidate import RawRecord
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RecordMatcher:
    """Clusters raw records into groups, each group representing one candidate."""

    def __init__(self, fuzzy_threshold: float = 88.0) -> None:
        """
        Args:
            fuzzy_threshold: Minimum RapidFuzz token-sort-ratio (0-100)
                required for two records to be matched purely on name
                similarity, when no stronger identifier matches.
        """
        self.fuzzy_threshold = fuzzy_threshold

    def match(self, records: List[RawRecord]) -> List[List[RawRecord]]:
        """Clusters records into groups representing the same candidate.

        Args:
            records: All normalized records from every source, for one
                pipeline run (may represent one or several candidates).

        Returns:
            A list of clusters; each cluster is a list of ``RawRecord``
            believed to belong to the same person.
        """
        clusters: List[List[RawRecord]] = []

        for record in records:
            target_cluster = self._find_matching_cluster(record, clusters)
            if target_cluster is not None:
                target_cluster.append(record)
            else:
                clusters.append([record])

        logger.info("Matched %d records into %d candidate cluster(s)", len(records), len(clusters))
        return clusters

    def _find_matching_cluster(
        self, record: RawRecord, clusters: List[List[RawRecord]]
    ) -> List[RawRecord] | None:
        """Finds the first existing cluster that ``record`` matches, if any."""
        for cluster in clusters:
            if any(self._is_match(record, existing) for existing in cluster):
                return cluster
        return None

    def _is_match(self, a: RawRecord, b: RawRecord) -> bool:
        """Determines whether two records refer to the same candidate."""
        if set(a.emails) & set(b.emails):
            return True
        if set(a.phones) & set(b.phones):
            return True
        if a.links.get("linkedin") and a.links.get("linkedin") == b.links.get("linkedin"):
            return True
        if a.links.get("github") and a.links.get("github") == b.links.get("github"):
            return True
        if a.full_name and b.full_name:
            score = fuzz.token_sort_ratio(a.full_name.lower(), b.full_name.lower())
            if score >= self.fuzzy_threshold:
                return True
        return False
