"""Date normalization using `python-dateutil`."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from dateutil import parser as date_parser

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DateNormalizer:
    """Normalizes loosely-formatted date strings into ``datetime.date`` objects."""

    PRESENT_KEYWORDS = {"present", "current", "now", "ongoing"}

    def normalize(self, raw: Optional[str]) -> Optional[date]:
        """Parses a free-form date string into a ``date``.

        Returns ``None`` for empty input or recognized "present/ongoing"
        markers (callers should treat ``None`` end dates as "current").

        Args:
            raw: A date string such as "2021-05", "May 2021", "2021/05/01".

        Returns:
            A ``date`` object, or ``None`` if unparsable / not applicable.
        """
        if raw is None:
            return None
        text = str(raw).strip()
        if not text or text.lower() in self.PRESENT_KEYWORDS:
            return None
        try:
            return date_parser.parse(text, default=datetime(1900, 1, 1)).date()
        except (ValueError, OverflowError):
            logger.debug("Could not parse date: %s", raw)
            return None
