"""Unit tests for the normalizer components."""

from __future__ import annotations

from src.normalizers.email_normalizer import EmailNormalizer, normalize_whitespace
from src.normalizers.phone_normalizer import PhoneNormalizer
from src.normalizers.skill_normalizer import SkillNormalizer


class TestPhoneNormalizer:
    def test_normalizes_us_number_to_e164(self):
        normalizer = PhoneNormalizer(default_region="US")
        assert normalizer.normalize("415-555-0192") == "+14155550192"

    def test_passes_through_already_e164(self):
        normalizer = PhoneNormalizer()
        assert normalizer.normalize("+14155550192") == "+14155550192"

    def test_returns_none_for_invalid_number(self):
        normalizer = PhoneNormalizer()
        assert normalizer.normalize("not-a-phone") is None

    def test_normalize_many_dedupes(self):
        normalizer = PhoneNormalizer()
        result = normalizer.normalize_many(["415-555-0192", "+14155550192"])
        assert result == ["+14155550192"]


class TestEmailNormalizer:
    def test_lowercases_and_trims(self):
        normalizer = EmailNormalizer()
        assert normalizer.normalize("  Jordan.Smith@GMAIL.com ") == "jordan.smith@gmail.com"

    def test_rejects_invalid_email(self):
        normalizer = EmailNormalizer()
        assert normalizer.normalize("not-an-email") is None

    def test_normalize_many_dedupes(self):
        normalizer = EmailNormalizer()
        result = normalizer.normalize_many(["a@b.com", "A@B.com", "bad"])
        assert result == ["a@b.com"]


class TestSkillNormalizer:
    def test_resolves_alias(self):
        normalizer = SkillNormalizer()
        assert normalizer.normalize("js") == "JavaScript"

    def test_title_cases_unknown_skill(self):
        normalizer = SkillNormalizer()
        assert normalizer.normalize("data engineering") == "Data Engineering"

    def test_normalize_many_dedupes_preserving_order(self):
        normalizer = SkillNormalizer()
        result = normalizer.normalize_many(["python", "Python", "js"])
        assert result == ["Python", "JavaScript"]


def test_normalize_whitespace_collapses_and_trims():
    assert normalize_whitespace("  Jordan   Smith  ") == "Jordan Smith"


def test_normalize_whitespace_none_passthrough():
    assert normalize_whitespace(None) is None
