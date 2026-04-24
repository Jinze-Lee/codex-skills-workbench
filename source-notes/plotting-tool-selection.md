# Plotting Tool Selection

## Purpose

Generic rules for choosing plotting tools across R, Python, spreadsheet software, PowerPoint, and vector editors.

Use project requirements to choose tools, not assumptions from another environment.

## Decision Rules

1. Use R when the plot is statistical, model-linked, or built from tidy/tabular data.
2. Use Python when plotting is part of a larger automation, image-processing, or machine-learning workflow.
3. Use PowerPoint or desktop automation when the primary output is a slide deck and layout iteration matters.
4. Use vector editors for final publication polish only after data-driven figures are generated reproducibly.
5. Use spreadsheet tools for quick inspection, not as the source of reproducible final analysis unless required.

## Inputs To Confirm

- Final destination: paper, slide deck, report, web page, exploratory analysis, or batch output
- Data volume and format
- Need for statistical modeling
- Need for visible desktop automation
- Reproducibility requirements
- Collaboration constraints

## Quality Control

- Check axis labels, units, legends, and color accessibility.
- Export at final-use dimensions.
- Keep scripts and output manifests together.
- Avoid manual edits that cannot be reproduced unless they are explicitly documented.

