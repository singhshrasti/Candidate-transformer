"""Applies runtime output configuration to a validated ``CanonicalCandidate``.

Handles, purely via ``config.json`` (no code changes required):
    - Field renaming
    - Field inclusion / exclusion
    - Enabling / disabling provenance in the output
    - Missing value policy: ``null`` | ``omit`` | ``error``
"""

from __future__ import annotations

from typing import Any, Dict

from src.models.candidate import CanonicalCandidate
from src.utils.config_loader import OutputFieldConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MissingRequiredFieldError(Exception):
    """Raised when the 'error' missing-value policy encounters a missing field."""


class OutputFormatter:
    """Transforms a canonical candidate dict according to runtime config."""

    def __init__(self, output_config: OutputFieldConfig, missing_value_policy: str) -> None:
        self.output_config = output_config
        self.missing_value_policy = missing_value_policy

    def format(self, candidate: CanonicalCandidate) -> Dict[str, Any]:
        """Produces the final output dictionary for one candidate.

        Args:
            candidate: A validated canonical candidate.

        Returns:
            A plain ``dict`` ready for JSON serialization, with renaming,
            inclusion/exclusion, provenance toggling, and missing-value
            policy applied.

        Raises:
            MissingRequiredFieldError: If ``missing_value_policy`` is
                ``"error"`` and a required field is empty/None.
        """
        data = candidate.model_dump(mode="json")

        if not self.output_config.include_provenance:
            data.pop("provenance", None)

        if self.output_config.include_fields:
            allowed = set(self.output_config.include_fields) | {"candidate_id"}
            if self.output_config.include_provenance:
                allowed.add("provenance")
            data = {k: v for k, v in data.items() if k in allowed}

        for field in self.output_config.exclude_fields:
            data.pop(field, None)

        data = self._apply_missing_value_policy(data)
        data = self._apply_renaming(data)
        return data

    def _apply_missing_value_policy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Applies the configured policy (null/omit/error) to empty fields."""
        result: Dict[str, Any] = {}
        for key, value in data.items():
            is_missing = value is None or value == [] or value == {}
            if not is_missing:
                result[key] = value
                continue

            if self.missing_value_policy == "null":
                result[key] = None
            elif self.missing_value_policy == "omit":
                continue
            elif self.missing_value_policy == "error":
                raise MissingRequiredFieldError(f"Required field '{key}' is missing")
            else:
                logger.warning(
                    "Unknown missing_value_policy '%s', defaulting to 'null'",
                    self.missing_value_policy,
                )
                result[key] = None
        return result

    def _apply_renaming(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Renames output keys according to the configured rename map."""
        if not self.output_config.rename_map:
            return data
        return {
            self.output_config.rename_map.get(key, key): value for key, value in data.items()
        }
