"""Applies all field-level normalizers to a single ``RawRecord``."""

from __future__ import annotations

from src.models.candidate import RawRecord
from src.normalizers.date_normalizer import DateNormalizer
from src.normalizers.email_normalizer import EmailNormalizer, normalize_whitespace
from src.normalizers.phone_normalizer import PhoneNormalizer
from src.normalizers.skill_normalizer import SkillNormalizer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RecordNormalizer:
    """Orchestrates normalization of every field on a ``RawRecord`` in place.

    This keeps each individual normalizer single-purpose (SRP) while
    providing one entry point the pipeline can call per record.
    """

    def __init__(
        self,
        phone_normalizer: PhoneNormalizer | None = None,
        skill_normalizer: SkillNormalizer | None = None,
        email_normalizer: EmailNormalizer | None = None,
    ) -> None:
        self.phone_normalizer = phone_normalizer or PhoneNormalizer()
        self.skill_normalizer = skill_normalizer or SkillNormalizer()
        self.email_normalizer = email_normalizer or EmailNormalizer()

    def normalize(self, record: RawRecord) -> RawRecord:
        """Returns a new ``RawRecord`` with all fields normalized.

        Args:
            record: The raw, parser-produced record.

        Returns:
            A new ``RawRecord`` instance with cleaned phones, emails,
            skills, names, location, and headline text.
        """
        logger.debug("Normalizing record from source=%s", record.source)
        data = record.model_dump()

        data["full_name"] = normalize_whitespace(data.get("full_name"))
        data["location"] = normalize_whitespace(data.get("location"))
        data["headline"] = normalize_whitespace(data.get("headline"))
        data["emails"] = self.email_normalizer.normalize_many(data.get("emails", []))
        data["phones"] = self.phone_normalizer.normalize_many(data.get("phones", []))
        data["skills"] = self.skill_normalizer.normalize_many(data.get("skills", []))
        data["links"] = {
            k: normalize_whitespace(v) for k, v in data.get("links", {}).items() if v
        }

        return RawRecord(**data)
