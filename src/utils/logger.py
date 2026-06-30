"""Centralized logging configuration using Rich for readable console output."""

from __future__ import annotations

import logging

from rich.logging import RichHandler

_CONFIGURED = False


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Returns a configured module-level logger.

    Args:
        name: Typically ``__name__`` of the calling module.
        level: Logging level for the root handler (only applied once).

    Returns:
        A standard library ``Logger`` instance backed by a Rich console
        handler, configured exactly once per process.
    """
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
        )
        _CONFIGURED = True
    return logging.getLogger(name)
