"""Validates a ``CanonicalCandidate`` against schema, email, phone, and type rules."""

from __future__ import annotations

from pydantic import ValidationError

from src.models.candidate import CanonicalCandidate
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CandidateValidationError(Exception):
    """Raised when a canonical candidate fails validation."""


class CandidateValidator:
    """Wraps Pydantic validation with friendlier error reporting."""

    def validate(self, candidate: CanonicalCandidate) -> CanonicalCandidate:
        """Re-validates an already-constructed candidate.

        Since ``CanonicalCandidate`` is a Pydantic model, most validation
        (email format, E.164 phone format, types, confidence range)
        already happened at construction time. This method exists to
        provide one clear point for the pipeline to call and re-validate
        after any further mutation (e.g. output formatting), raising a
        single, pipeline-specific exception type.

        Args:
            candidate: The candidate to validate.

        Returns:
            The same candidate, if valid.

        Raises:
            CandidateValidationError: If validation fails.
        """
        try:
            CanonicalCandidate.model_validate(candidate.model_dump())
        except ValidationError as exc:
            logger.error("Candidate %s failed validation: %s", candidate.candidate_id, exc)
            raise CandidateValidationError(str(exc)) from exc
        return candidate
