# Candidate Transformer

Candidate Transformer is a Python data pipeline that combines candidate data
from multiple sources into one canonical JSON candidate profile.

It supports sample inputs from:

- Recruiter CSV
- ATS JSON
- Resume PDF
- Recruiter notes TXT
- LinkedIn JSON
- GitHub JSON

The pipeline parses, normalizes, matches, merges, validates, and writes the
final candidate profile to `output/canonical_candidate.json`.

## Project Structure

```text
candidate-transformer/
  config/
    config.json
  data/
    ats.json
    github.json
    linkedin.json
    notes.txt
    recruiter.csv
    resume.pdf
  output/
    canonical_candidate.json
  src/
    main.py
    parsers/
    normalizers/
    matchers/
    mergers/
    models/
    pipeline/
    utils/
    validators/
  tests/
  cli.py
  requirements.txt
  README.md
```

## Requirements

- Python 3.11 or newer
- pip

## Setup

Open PowerShell in the project folder:

```powershell
cd C:\Users\shras\Downloads\candidate-transformer\candidate-transformer
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

If PowerShell blocks activation scripts, run this once for the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run With Sample Data

Run the default pipeline:

```powershell
python -m src.main
```

You can also run it without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m src.main
```

The command reads all sample files from `data/` and writes the final output to:

```text
output/canonical_candidate.json
```

Successful output includes lines like:

```text
Matched 6 records into 1 candidate cluster(s)
Pipeline produced 1 canonical candidate(s)
Wrote canonical output to output\canonical_candidate.json
Pipeline complete.
```

## Run With Custom Files

Use the CLI when you want to pass specific source files:

```powershell
python cli.py `
  --resume data/resume.pdf `
  --ats data/ats.json `
  --csv data/recruiter.csv `
  --linkedin data/linkedin.json `
  --github data/github.json `
  --notes data/notes.txt `
  --config config/config.json `
  --output output/canonical_candidate.json
```

All source arguments are optional. For example, you can run only ATS and resume:

```powershell
python cli.py `
  --ats data/ats.json `
  --resume data/resume.pdf
```

## Run Tests

Run the test suite:

```powershell
python -m pytest -q
```

Expected result:

```text
41 passed
```

## Configuration

Runtime behavior is controlled by:

```text
config/config.json
```

The config includes:

- Source priority for conflict resolution
- Source reliability weights
- Fuzzy name matching threshold
- Missing value policy
- Output field inclusion, exclusion, and renaming
- Provenance output settings

## Output

The generated canonical candidate JSON includes:

- Candidate ID
- Full name
- Emails
- Phone numbers
- Location
- LinkedIn and GitHub links
- Headline
- Years of experience
- Skills
- Experience history
- Education history
- Field provenance
- Overall confidence score

## Notes

- `output/canonical_candidate.json` is generated when the pipeline runs.
- `.venv/`, Python cache files, pytest cache, and generated output JSON files
  are ignored by git.
- The included sample data is for one candidate, Jordan Smith, and is designed
  to test parsing, matching, conflict resolution, provenance, and confidence
  scoring.
