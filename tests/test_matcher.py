"""Unit tests for the record matcher."""

from __future__ import annotations

from src.matchers.record_matcher import RecordMatcher
from src.models.candidate import RawRecord, SourceType


def _record(**kwargs) -> RawRecord:
    defaults = dict(source=SourceType.CSV)
    defaults.update(kwargs)
    return RawRecord(**defaults)


class TestRecordMatcher:
    def test_matches_by_shared_email(self):
        matcher = RecordMatcher()
        records = [
            _record(source=SourceType.CSV, full_name="Jordan Smith", emails=["a@b.com"]),
            _record(source=SourceType.ATS, full_name="J. Smith", emails=["a@b.com"]),
        ]
        clusters = matcher.match(records)
        assert len(clusters) == 1
        assert len(clusters[0]) == 2

    def test_matches_by_shared_phone(self):
        matcher = RecordMatcher()
        records = [
            _record(source=SourceType.CSV, phones=["+14155550192"]),
            _record(source=SourceType.RESUME, phones=["+14155550192"]),
        ]
        clusters = matcher.match(records)
        assert len(clusters) == 1

    def test_matches_by_linkedin_url(self):
        matcher = RecordMatcher()
        records = [
            _record(source=SourceType.CSV, links={"linkedin": "https://linkedin.com/in/x"}),
            _record(source=SourceType.LINKEDIN, links={"linkedin": "https://linkedin.com/in/x"}),
        ]
        clusters = matcher.match(records)
        assert len(clusters) == 1

    def test_matches_by_fuzzy_name(self):
        matcher = RecordMatcher(fuzzy_threshold=85.0)
        records = [
            _record(source=SourceType.CSV, full_name="Jordan A. Smith"),
            _record(source=SourceType.NOTES, full_name="Jordan Smith"),
        ]
        clusters = matcher.match(records)
        assert len(clusters) == 1

    def test_distinct_candidates_not_merged(self):
        matcher = RecordMatcher()
        records = [
            _record(source=SourceType.CSV, full_name="Jordan Smith", emails=["jordan@x.com"]),
            _record(source=SourceType.ATS, full_name="Taylor Reed", emails=["taylor@y.com"]),
        ]
        clusters = matcher.match(records)
        assert len(clusters) == 2
