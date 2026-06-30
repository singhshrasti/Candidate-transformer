"""Runtime configuration loading and access.

All pipeline behavior that should be tunable "without changing code" is
driven through a single ``PipelineConfig`` object loaded from
``config/config.json`` (or a user-supplied path). This includes field
renaming, field inclusion/exclusion, provenance toggling, missing-value
policy, and source priority/reliability ordering.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class MissingValuePolicy(BaseModel):
    """Defines how missing canonical fields should be handled at output time."""

    policy: str = Field(default="null", description="One of: null, omit, error")


class OutputFieldConfig(BaseModel):
    """Controls field renaming and inclusion/exclusion in the final output."""

    include_fields: List[str] = Field(default_factory=list)
    exclude_fields: List[str] = Field(default_factory=list)
    rename_map: Dict[str, str] = Field(default_factory=dict)
    include_provenance: bool = True


class PipelineConfig(BaseModel):
    """Top level runtime configuration for the entire pipeline."""

    source_priority: List[str] = Field(
        default_factory=lambda: [
            "resume",
            "ats",
            "linkedin",
            "github",
            "csv",
            "notes",
        ]
    )
    source_reliability: Dict[str, float] = Field(
        default_factory=lambda: {
            "ats": 1.0,
            "resume": 0.95,
            "linkedin": 0.90,
            "github": 0.85,
            "csv": 0.80,
            "notes": 0.70,
        }
    )
    missing_value_policy: MissingValuePolicy = Field(default_factory=MissingValuePolicy)
    output_fields: OutputFieldConfig = Field(default_factory=OutputFieldConfig)
    fuzzy_match_threshold: float = Field(
        default=88.0, description="RapidFuzz name-similarity score (0-100) required for a match."
    )

    @classmethod
    def load(cls, path: str | Path) -> "PipelineConfig":
        """Loads configuration from a JSON file on disk.

        Args:
            path: Path to a ``config.json`` file.

        Returns:
            A validated ``PipelineConfig`` instance. If the file does not
            exist, returns a config built entirely from defaults.
        """
        path = Path(path)
        if not path.exists():
            return cls()
        with path.open("r", encoding="utf-8") as fh:
            raw: Dict[str, Any] = json.load(fh)
        return cls(**raw)
