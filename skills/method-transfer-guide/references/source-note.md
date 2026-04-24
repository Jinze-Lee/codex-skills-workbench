# Method Transfer Guide

## Purpose

Generic guidance for transferring an analysis, plotting style, or automation pattern from one project to another without copying stale assumptions.

This version is deliberately path-neutral and project-neutral.

## Inputs To Confirm

- Source method or script: `<source-method>`
- Target project root: `<target-project-root>`
- Target data structure: `<target-data>`
- Required outputs: `<output-list>`
- Constraints: packages, runtime, style guide, reproducibility requirements

## Workflow

1. Extract the underlying method, not the historical file paths.
2. List assumptions in the source workflow: variable names, units, encodings, grouping, thresholds, and output expectations.
3. Map each assumption to the target project.
4. Replace hard-coded constants with parameters or manifest entries.
5. Run on a small test subset before full execution.
6. Compare outputs against expected structure, not against old project-specific values.
7. Document what changed during transfer.

## Anti-Copy Rules

- Do not reuse absolute paths from prior projects.
- Do not assume old column names exist in the new dataset.
- Do not keep old species, site, treatment, or file identifiers unless the user confirms they apply.
- Do not silently change scientific meaning just to make code run.

