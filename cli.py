"""Command-line interface for the candidate transformation pipeline.

Usage:
    python cli.py --resume data/resume.pdf --ats data/ats.json --csv data/recruiter.csv
    python cli.py --resume data/resume.pdf --ats data/ats.json --csv data/recruiter.csv \\
        --linkedin data/linkedin.json --github data/github.json --notes data/notes.txt \\
        --config config/config.json --output output/canonical_candidate.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.json import JSON

from src.pipeline.pipeline import CandidateTransformationPipeline
from src.utils.config_loader import PipelineConfig
from src.utils.logger import get_logger

app = typer.Typer(add_completion=False, help="Candidate Data Transformation Pipeline CLI")
console = Console()
logger = get_logger(__name__)


@app.command()
def transform(
    csv: Optional[Path] = typer.Option(None, "--csv", help="Path to recruiter CSV file"),
    ats: Optional[Path] = typer.Option(None, "--ats", help="Path to ATS JSON file"),
    resume: Optional[Path] = typer.Option(None, "--resume", help="Path to resume PDF file"),
    notes: Optional[Path] = typer.Option(None, "--notes", help="Path to recruiter notes TXT file"),
    linkedin: Optional[Path] = typer.Option(None, "--linkedin", help="Path to LinkedIn JSON file"),
    github: Optional[Path] = typer.Option(None, "--github", help="Path to GitHub JSON file"),
    config: Path = typer.Option(
        Path("config/config.json"), "--config", help="Path to pipeline config.json"
    ),
    output: Path = typer.Option(
        Path("output/canonical_candidate.json"), "--output", help="Output JSON file path"
    ),
) -> None:
    """Runs the candidate transformation pipeline over the given source files."""
    pipeline_config = PipelineConfig.load(config)
    pipeline = CandidateTransformationPipeline(pipeline_config)

    source_paths = {
        "csv": str(csv) if csv else None,
        "ats": str(ats) if ats else None,
        "resume": str(resume) if resume else None,
        "notes": str(notes) if notes else None,
        "linkedin": str(linkedin) if linkedin else None,
        "github": str(github) if github else None,
    }
    source_paths = {k: v for k, v in source_paths.items() if v}

    if not source_paths:
        console.print("[bold red]Error:[/bold red] No source files provided.")
        raise typer.Exit(code=1)

    console.print(f"[bold cyan]Running pipeline with sources:[/bold cyan] {list(source_paths)}")
    results = pipeline.run(source_paths)
    pipeline.write_output(results, output)

    console.print(f"[bold green]Done.[/bold green] Output written to {output}")
    payload = results[0] if len(results) == 1 else results
    console.print(JSON.from_data(payload))


if __name__ == "__main__":
    app()
