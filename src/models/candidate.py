"""
Canonical candidate data models.

This module defines the Pydantic models used to represent a single,
de-duplicated, validated "canonical" candidate profile, as well as the
intermediate "raw record" representation produced by each parser before
matching and merging takes place.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class SourceType(str, Enum):
    """Enumerates every supported data source.

    The string value is used both as the dictionary key for provenance
    tracking and as the key used in ``config.json`` to configure source
    priority and reliability weighting.
    """

    RESUME = "resume"
    ATS = "ats"
    LINKEDIN = "linkedin"
    GITHUB = "github"
    CSV = "csv"
    NOTES = "notes"


class ExperienceEntry(BaseModel):
    """A single work-experience entry."""

    company: str
    title: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    source: Optional[SourceType] = None


class EducationEntry(BaseModel):
    """A single education entry."""

    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    source: Optional[SourceType] = None


class RawRecord(BaseModel):
    """A normalized, but not-yet-merged, record originating from one source.

    Every parser/normalizer pair produces one ``RawRecord``. The record
    matcher groups ``RawRecord`` instances that refer to the same human
    being, and the merge engine combines those groups into a single
    ``CanonicalCandidate``.
    """

    source: SourceType
    full_name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    links: Dict[str, str] = Field(default_factory=dict)
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    raw_payload: Dict = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


class CanonicalCandidate(BaseModel):
    """The final, validated, canonical candidate profile.

    This is the schema that is serialized to ``output/canonical_candidate.json``.
    Field names are subject to the rename/include/exclude rules defined in
    ``config.json`` and applied by ``OutputFormatter`` at serialization time;
    this model itself always uses the canonical field names internally.
    """

    candidate_id: str
    full_name: Optional[str] = None
    emails: List[EmailStr] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    links: Dict[str, str] = Field(default_factory=dict)
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    provenance: Dict[str, str] = Field(default_factory=dict)
    overall_confidence: float = 0.0

    @field_validator("phones")
    @classmethod
    def _validate_phone_format(cls, value: List[str]) -> List[str]:
        """Ensures every phone number is in E.164 format (e.g. +14155551234)."""
        for phone in value:
            if not phone.startswith("+"):
                raise ValueError(
                    f"Phone number '{phone}' is not in E.164 format (must start with '+')"
                )
        return value

    @field_validator("overall_confidence")
    @classmethod
    def _validate_confidence_range(cls, value: float) -> float:
        """Ensures the overall confidence score is within [0.0, 1.0]."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("overall_confidence must be between 0.0 and 1.0")
        return value
