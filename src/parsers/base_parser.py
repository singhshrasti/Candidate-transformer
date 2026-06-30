"""Abstract base class for all source parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.models.candidate import RawRecord


class BaseParser(ABC):
    """Defines the contract every source-specific parser must implement.

    Each concrete parser is responsible for reading one file format
    (CSV, JSON, PDF, TXT) and producing a single ``RawRecord`` populated
    with whatever fields it can extract. Field-level normalization
    (phone formatting, date parsing, etc.) is intentionally NOT done
    here; that is the responsibility of the ``normalizers`` package so
    parsers stay focused purely on extraction.
    """

    @abstractmethod
    def parse(self, path: str | Path) -> RawRecord:
        """Parses a file at ``path`` into a ``RawRecord``.

        Args:
            path: Filesystem path to the source file.

        Returns:
            A populated ``RawRecord`` with ``source`` set appropriately.

        Raises:
            FileNotFoundError: If ``path`` does not exist.
            ValueError: If the file content cannot be parsed.
        """
        raise NotImplementedError
