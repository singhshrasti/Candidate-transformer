"""Unit tests for source parsers, using the sample files in data/."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.models.candidate import SourceType
from src.parsers.ats_parser import ATSJSONParser
from src.parsers.csv_parser import RecruiterCSVParser
from src.parsers.github_parser import GitHubParser
from src.parsers.linkedin_parser import LinkedInParser
from src.parsers.notes_parser import RecruiterNotesParser
from src.parsers.resume_parser import ResumePDFParser

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestCSVParser:
    def test_parses_sample_csv(self):
        record = RecruiterCSVParser().parse(DATA_DIR / "recruiter.csv")
        assert record.source == SourceType.CSV
        assert record.full_name == "Jordan A. Smith"
        assert "jordan.smith@gmail.com" in record.emails

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            RecruiterCSVParser().parse(DATA_DIR / "does_not_exist.csv")


class TestATSParser:
    def test_parses_sample_ats(self):
        record = ATSJSONParser().parse(DATA_DIR / "ats.json")
        assert record.source == SourceType.ATS
        assert record.full_name == "Jordan Smith"
        assert len(record.experience) == 2
        assert len(record.education) == 1


class TestLinkedInParser:
    def test_parses_sample_linkedin(self):
        record = LinkedInParser().parse(DATA_DIR / "linkedin.json")
        assert record.source == SourceType.LINKEDIN
        assert record.links.get("linkedin") == "https://linkedin.com/in/jordansmith"
        assert len(record.experience) >= 1


class TestGitHubParser:
    def test_parses_sample_github(self):
        record = GitHubParser().parse(DATA_DIR / "github.json")
        assert record.source == SourceType.GITHUB
        assert "Python" in record.skills
        assert record.links.get("github") == "https://github.com/jordansmith"


class TestNotesParser:
    def test_parses_sample_notes(self):
        record = RecruiterNotesParser().parse(DATA_DIR / "notes.txt")
        assert record.source == SourceType.NOTES
        assert "jordan.smith@gmail.com" in record.emails


class TestResumeParser:
    def test_parses_sample_resume(self):
        record = ResumePDFParser().parse(DATA_DIR / "resume.pdf")
        assert record.source == SourceType.RESUME
        assert record.full_name == "Jordan Smith"
        assert "jordan.smith@gmail.com" in record.emails
