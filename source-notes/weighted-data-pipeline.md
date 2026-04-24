# Weighted Data Pipeline

## Purpose

Generic end-to-end workflow for preparing weighted analysis data, calculating summary metrics, merging outputs, and producing final figures.

This public version removes local file paths, exact row counts, and project-specific intermediate filenames.

## Inputs To Confirm

- Raw data files: `<raw-data-list>`
- Metadata or lookup tables: `<metadata-files>`
- Weight definition: `<weight-rule>`
- Analysis level: species, group, site, sample, or other unit
- Output root: `<output-root>`

## Workflow

1. Create a project manifest that lists every input, intermediate output, and final output.
2. Deduplicate records using explicit keys and export a deduplication report.
3. Clean variable names, encodings, units, and missing values.
4. Calculate summary metrics and their uncertainty.
5. Merge intermediate tables using checked keys.
6. Extract or calculate weights and verify their interpretation.
7. Run weighted analyses and export model summaries.
8. Produce final figures and a compact README for the output folder.

## Output Checklist

- Cleaned data table
- Deduplication or exclusion report
- Intermediate metric tables
- Merged wide or long analysis table
- Weight table
- Model summaries
- Figures
- Reproducibility log

## Path Policy

Use `<project-root>/data`, `<project-root>/intermediate`, and `<project-root>/outputs` style placeholders. Do not publish local machine paths.

