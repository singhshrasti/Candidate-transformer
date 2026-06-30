"""Unit tests for the output formatter (runtime config) and candidate validator."""

from __future__ import annotations

import pytest

from src.models.candidate import CanonicalCandidate
from src.utils.config_loader import OutputFieldConfig
from src.validators.candidate_validator import CandidateValidationError, CandidateValidator
from src.validators.output_formatter import MissingRequiredFieldError, OutputFormatter


def _candidate(**overrides) -> CanonicalCandidate:
    defaults = dict(
        candidate_id="abc-123",
        full_name="Jordan Smith",
        emails=["jordan@x.com"],
        phones=["+14155550192"],
        overall_confidence=0.9,
    )
    defaults.update(overrides)
    return CanonicalCandidate(**defaults)


class TestOutputFormatter:
    def test_null_policy_keeps_missing_fields_as_none(self):
        formatter = OutputFormatter(OutputFieldConfig(), "null")
        result = formatter.format(_candidate(location=None))
        assert result["location"] is None

    def test_omit_policy_removes_missing_fields(self):
        formatter = OutputFormatter(OutputFieldConfig(), "omit")
        result = formatter.format(_candidate(location=None))
        assert "location" not in result

    def test_error_policy_raises_on_missing_field(self):
        formatter = OutputFormatter(OutputFieldConfig(), "error")
        with pytest.raises(MissingRequiredFieldError):
            formatter.format(_candidate(location=None))

    def test_include_fields_restricts_output(self):
        config = OutputFieldConfig(include_fields=["full_name", "emails"])
        formatter = OutputFormatter(config, "omit")
        result = formatter.format(_candidate())
        assert set(result.keys()) <= {"candidate_id", "full_name", "emails", "provenance"}

    def test_exclude_fields_removes_keys(self):
        config = OutputFieldConfig(exclude_fields=["phones"])
        formatter = OutputFormatter(config, "null")
        result = formatter.format(_candidate())
        assert "phones" not in result

    def test_rename_map_renames_keys(self):
        config = OutputFieldConfig(rename_map={"full_name": "candidate_name"})
        formatter = OutputFormatter(config, "null")
        result = formatter.format(_candidate())
        assert "candidate_name" in result
        assert "full_name" not in result

    def test_provenance_can_be_disabled(self):
        config = OutputFieldConfig(include_provenance=False)
        formatter = OutputFormatter(config, "null")
        result = formatter.format(_candidate())
        assert "provenance" not in result


class TestCandidateValidator:
    def test_valid_candidate_passes(self):
        validator = CandidateValidator()
        candidate = _candidate()
        assert validator.validate(candidate) is candidate

    def test_invalid_phone_raises_at_construction(self):
        with pytest.raises(Exception):
            _candidate(phones=["555-0192"])  # not E.164, missing '+'
