"""Phone number normalization to E.164 format using the `phonenumbers` library."""

from __future__ import annotations

from typing import List, Optional

import phonenumbers

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PhoneNormalizer:
    """Normalizes raw phone number strings to E.164 format (e.g. +14155552671)."""

    def __init__(self, default_region: str = "US") -> None:
        """
        Args:
            default_region: ISO 3166-1 alpha-2 region used when a number
                has no country code (e.g. local US numbers without '+1').
        """
        self.default_region = default_region

    def normalize(self, raw: str) -> Optional[str]:
        """Normalizes a single phone number string.

        Returns:
            The E.164-formatted number, or ``None`` if it cannot be parsed
            as a valid phone number.
        """
        if not raw or not raw.strip():
            return None
        try:
            parsed = phonenumbers.parse(raw, self.default_region)
            if not phonenumbers.is_valid_number(parsed):
                logger.debug("Invalid phone number skipped: %s", raw)
                return None
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            logger.debug("Could not parse phone number: %s", raw)
            return None

    def normalize_many(self, raws: List[str]) -> List[str]:
        """Normalizes a list of phone numbers, dropping invalid/duplicate entries."""
        normalized = (self.normalize(raw) for raw in raws)
        return list(dict.fromkeys(n for n in normalized if n))
