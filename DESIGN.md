# Design Document — Candidate Data Transformation Pipeline

## Pipeline

The pipeline runs nine sequential stages, each implemented as an independent
component: **Load** (read files from disk) → **Parse** (one parser per source
format, producing a `RawRecord`) → **Normalize** (clean phones, dates,
skills, emails, whitespace) → **Record Matching** (cluster records belonging
to the same candidate via email → phone → LinkedIn URL → GitHub URL → fuzzy
name similarity) → **Conflict Resolution & Merge** (combine a matched
cluster into one `CanonicalCandidate`, scalar fields resolved by configured
source priority, list fields unioned) → **Confidence Scoring** (reliability-
weighted average across contributing sources) → **Provenance Tracking**
(per-field source attribution) → **Pydantic Validation** (schema, email,
phone, type checks) → **Canonical JSON Output**. `CandidateTransformationPipeline`
is the sole orchestrator; every other component only knows its own stage.

## Canonical Schema

`CanonicalCandidate` (Pydantic model) defines: `candidate_id`, `full_name`,
`emails` (validated `EmailStr` list), `phones` (validated E.164 strings),
`location`, `links` (dict of platform → URL), `headline`,
`years_experience`, `skills`, `experience` (list of `ExperienceEntry`),
`education` (list of `EducationEntry`), `provenance` (dict mapping field
name → contributing source(s)), and `overall_confidence` (float, 0–1).
Each source parser instead produces a looser `RawRecord` — the canonical
schema is only constructed once after matching and merging.

## Conflict Resolution

Scalar fields (name, location, headline, years of experience) are resolved
by iterating a matched cluster's records in the order defined by
`config.json`'s `source_priority` list and taking the first non-empty
value — i.e. highest-priority source wins. List fields (emails, phones,
skills, links, experience, education) are unioned across every contributing
source rather than overwritten, since recruiters benefit from maximum
coverage on these fields. Both behaviors are entirely driven by
`source_priority` in config — no code changes are required to reorder
source trust (e.g. promoting LinkedIn above ATS).

## Normalization Strategy

Each field type has a dedicated, single-purpose normalizer: `PhoneNormalizer`
(via the `phonenumbers` library, producing E.164), `DateNormalizer` (via
`python-dateutil`, tolerant of "present/current" markers), `SkillNormalizer`
(alias resolution + title-casing + de-duplication), and `EmailNormalizer`
(lowercasing + RFC-shape validation). A `RecordNormalizer` composes these
into one call per `RawRecord` so the pipeline only needs a single
normalization step, while each underlying normalizer remains independently
testable and reusable.

## Runtime Configuration

`PipelineConfig` (loaded from `config/config.json`) controls source
priority, source reliability weights (for confidence scoring), the missing
value policy (`null` / `omit` / `error`), and an `OutputFieldConfig` block
governing field inclusion, exclusion, renaming, and provenance visibility.
`OutputFormatter` applies all of this after validation, so the canonical
internal schema stays stable while the *external* JSON shape is fully
configurable without touching code.

## Future Improvements

- Replace regex-based resume/notes extraction with an ML-based resume
  parser (e.g. a fine-tuned NER model) for higher recall on unusual formats.
- Move record matching to a blocking + index-based approach (e.g. by email
  domain or phone prefix) to scale beyond small batches.
- Add a persistence layer (e.g. a database) so the pipeline can de-duplicate
  against previously seen candidates across multiple runs, not just within
  one batch.
- Extend confidence scoring to account for field-level agreement/conflict
  across sources (e.g. lower confidence when sources disagree on a value),
  not just source reliability.
