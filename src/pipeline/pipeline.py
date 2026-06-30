"""End-to-end pipeline orchestration.

Stage order: Load -> Parse -> Normalize -> Match -> Merge (conflict
resolution + provenance + confidence) -> Validate -> Format -> Output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from src.matchers.record_matcher import RecordMatcher
from src.mergers.merge_engine import MergeEngine
from src.models.candidate import RawRecord
from src.normalizers.record_normalizer import RecordNormalizer
from src.parsers.ats_parser import ATSJSONParser
from src.parsers.csv_parser import RecruiterCSVParser
from src.parsers.github_parser import GitHubParser
from src.parsers.linkedin_parser import LinkedInParser
from src.parsers.notes_parser import RecruiterNotesParser
from src.parsers.resume_parser import ResumePDFParser
from src.utils.config_loader import PipelineConfig
from src.utils.logger import get_logger
from src.validators.candidate_validator import CandidateValidator
from src.validators.output_formatter import OutputFormatter

logger = get_logger(__name__)


class CandidateTransformationPipeline:
    """Orchestrates the full candidate data transformation pipeline."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.normalizer = RecordNormalizer()
        self.matcher = RecordMatcher(fuzzy_threshold=config.fuzzy_match_threshold)
        self.merge_engine = MergeEngine(
            source_priority=config.source_priority,
            source_reliability=config.source_reliability,
        )
        self.validator = CandidateValidator()
        self.formatter = OutputFormatter(
            output_config=config.output_fields,
            missing_value_policy=config.missing_value_policy.policy,
        )
        self._parsers = {
            "csv": RecruiterCSVParser(),
            "ats": ATSJSONParser(),
            "resume": ResumePDFParser(),
            "notes": RecruiterNotesParser(),
            "linkedin": LinkedInParser(),
            "github": GitHubParser(),
        }

    def run(self, source_paths: Dict[str, str]) -> List[Dict]:
        """Runs the full pipeline over the supplied source file paths.

        Args:
            source_paths: Mapping of source name (one of "csv", "ats",
                "resume", "notes", "linkedin", "github") to file path.
                Sources not present in the mapping are skipped.

        Returns:
            A list of formatted, validated canonical candidate dicts
            (one per matched cluster of input records).
        """
        raw_records = self._load_and_parse(source_paths)
        normalized_records = [self.normalizer.normalize(r) for r in raw_records]
        clusters = self.matcher.match(normalized_records)

        results = []
        for cluster in clusters:
            candidate = self.merge_engine.merge(cluster)
            candidate = self.validator.validate(candidate)
            formatted = self.formatter.format(candidate)
            results.append(formatted)

        logger.info("Pipeline produced %d canonical candidate(s)", len(results))
        return results

    def _load_and_parse(self, source_paths: Dict[str, str]) -> List[RawRecord]:
        """Loads and parses each configured source file, skipping missing ones."""
        records: List[RawRecord] = []
        for source_name, path in source_paths.items():
            if not path:
                continue
            parser = self._parsers.get(source_name)
            if parser is None:
                logger.warning("No parser registered for source '%s', skipping", source_name)
                continue
            try:
                record = parser.parse(path)
                records.append(record)
            except FileNotFoundError as exc:
                logger.warning("Skipping missing source '%s': %s", source_name, exc)
            except Exception as exc:  # noqa: BLE001 - surface but don't crash the run
                logger.error("Failed to parse source '%s' (%s): %s", source_name, path, exc)
        return records

    def write_output(self, results: List[Dict], output_path: str | Path) -> None:
        """Writes the pipeline results to a JSON file.

        Args:
            results: The list of formatted candidate dicts.
            output_path: Destination JSON file path. Parent directories
                are created automatically.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = results[0] if len(results) == 1 else results
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        logger.info("Wrote canonical output to %s", output_path)
