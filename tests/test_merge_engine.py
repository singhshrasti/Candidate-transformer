"""Unit tests for the merge engine: conflict resolution, provenance, confidence."""

from __future__ import annotations

from src.mergers.merge_engine import MergeEngine
from src.models.candidate import RawRecord, SourceType

SOURCE_PRIORITY = ["resume", "ats", "linkedin", "github", "csv", "notes"]
SOURCE_RELIABILITY = {
    "ats": 1.0,
    "resume": 0.95,
    "linkedin": 0.90,
    "github": 0.85,
    "csv": 0.80,
    "notes": 0.70,
}


def _engine() -> MergeEngine:
    return MergeEngine(source_priority=SOURCE_PRIORITY, source_reliability=SOURCE_RELIABILITY)


class TestMergeEngine:
    def test_scalar_conflict_resolved_by_priority(self):
        cluster = [
            RawRecord(source=SourceType.CSV, full_name="J. Smith"),
            RawRecord(source=SourceType.ATS, full_name="Jordan Smith"),
        ]
        candidate = _engine().merge(cluster)
        assert candidate.full_name == "Jordan Smith"
        assert candidate.provenance["full_name"] == "ats"

    def test_resume_outranks_ats_per_default_priority(self):
        cluster = [
            RawRecord(source=SourceType.ATS, headline="ATS Headline"),
            RawRecord(source=SourceType.RESUME, headline="Resume Headline"),
        ]
        candidate = _engine().merge(cluster)
        assert candidate.headline == "Resume Headline"

    def test_list_fields_are_unioned(self):
        cluster = [
            RawRecord(source=SourceType.CSV, skills=["Python", "SQL"]),
            RawRecord(source=SourceType.GITHUB, skills=["Go", "Python"]),
        ]
        candidate = _engine().merge(cluster)
        assert set(candidate.skills) == {"Python", "SQL", "Go"}
        assert "csv" in candidate.provenance["skills"]
        assert "github" in candidate.provenance["skills"]

    def test_confidence_score_within_bounds(self):
        cluster = [
            RawRecord(source=SourceType.ATS, full_name="Jordan Smith", emails=["a@b.com"]),
        ]
        candidate = _engine().merge(cluster)
        assert 0.0 <= candidate.overall_confidence <= 1.0
        assert candidate.overall_confidence == 1.0  # only ATS field, weight 1.0

    def test_candidate_id_is_generated(self):
        cluster = [RawRecord(source=SourceType.CSV, full_name="Jordan Smith")]
        candidate = _engine().merge(cluster)
        assert candidate.candidate_id
