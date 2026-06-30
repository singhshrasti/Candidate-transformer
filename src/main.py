"""Default entry point: ``python -m src.main``.

Runs the pipeline against the sample files shipped in ``data/`` using the
default ``config/config.json``, writing to ``output/canonical_candidate.json``.
For custom source selection, use ``cli.py`` instead.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.json import JSON

from src.pipeline.pipeline import CandidateTransformationPipeline
from src.utils.config_loader import PipelineConfig
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)

DEFAULT_SOURCES = {
    "csv": "data/recruiter.csv",
    "ats": "data/ats.json",
    "resume": "data/resume.pdf",
    "notes": "data/notes.txt",
    "linkedin": "data/linkedin.json",
    "github": "data/github.json",
}


def main() -> None:
    """Runs the pipeline end-to-end using default sample data and config."""
    config = PipelineConfig.load("config/config.json")
    pipeline = CandidateTransformationPipeline(config)

    available_sources = {
        name: path for name, path in DEFAULT_SOURCES.items() if Path(path).exists()
    }
    if not available_sources:
        console.print(
            "[bold red]No sample data files found in data/.[/bold red] "
            "Run cli.py with explicit paths instead."
        )
        return

    console.print(f"[bold cyan]Running with sample sources:[/bold cyan] {list(available_sources)}")
    results = pipeline.run(available_sources)
    pipeline.write_output(results, "output/canonical_candidate.json")

    console.print("[bold green]Pipeline complete.[/bold green]")
    payload = results[0] if len(results) == 1 else results
    console.print(JSON.from_data(payload))


if __name__ == "__main__":
    main()
