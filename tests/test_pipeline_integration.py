"""End-to-end integration tests for the full pipeline."""

from __future__ import annotations

from pathlib import Path

from src.pipeline.pipeline import CandidateTransformationPipeline
from src.utils.config_loader import PipelineConfig

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.json"


def _all_sources() -> dict:
    return {
        "csv": str(DATA_DIR / "recruiter.csv"),
        "ats": str(DATA_DIR / "ats.json"),
        "resume": str(DATA_DIR / "resume.pdf"),
        "notes": str(DATA_DIR / "notes.txt"),
        "linkedin": str(DATA_DIR / "linkedin.json"),
        "github": str(DATA_DIR / "github.json"),
    }


class TestPipelineIntegration:
    def test_full_pipeline_merges_all_sources_into_one_candidate(self):
        config = PipelineConfig.load(CONFIG_PATH)
        pipeline = CandidateTransformationPipeline(config)
        results = pipeline.run(_all_sources())

        assert len(results) == 1
        candidate = results[0]
        assert candidate["full_name"]
        assert "jordan.smith@gmail.com" in candidate["emails"]
        assert candidate["overall_confidence"] > 0
        assert "provenance" in candidate

    def test_pipeline_handles_missing_sources_gracefully(self):
        config = PipelineConfig.load(CONFIG_PATH)
        pipeline = CandidateTransformationPipeline(config)
        sources = {"csv": str(DATA_DIR / "recruiter.csv")}
        results = pipeline.run(sources)
        assert len(results) == 1

    def test_write_output_creates_file(self, tmp_path):
        config = PipelineConfig.load(CONFIG_PATH)
        pipeline = CandidateTransformationPipeline(config)
        results = pipeline.run(_all_sources())
        out_file = tmp_path / "canonical_candidate.json"
        pipeline.write_output(results, out_file)
        assert out_file.exists()
