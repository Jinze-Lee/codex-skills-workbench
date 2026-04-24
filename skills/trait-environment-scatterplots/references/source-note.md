# Trait Environment Scatterplots

## Purpose

Generic workflow for trait-environment, response-predictor, or grouped scatterplots with regression and publication-ready export.

Use placeholders below and adapt variables, datasets, and paths to the active project context.

## Inputs To Confirm

- Response or trait variable: `<response-or-trait-variable>`
- Predictor or environmental variable: `<predictor-or-environment-variable>`
- Grouping level: species, genus, family, site, treatment, experimental group, or another grouping variable
- Data table: `<input-table>`
- Output directory: `<output-dir>`
- Regression choice: pooled, grouped, mixed model, weighted model, robust model, or nonparametric smoother

## Workflow

1. Inspect variable types, missing values, outliers, and group sample sizes.
2. Decide whether variables should be used directly, transformed, standardized, or modeled on another scale according to the scientific question.
3. Fit the appropriate relationship for the analysis level and study design.
4. Show raw points, group encodings, fitted trends, uncertainty, and sample-size context.
5. Export both the figure and the model/statistics table.
6. Write a short interpretation that distinguishes visual pattern from statistical evidence.

## Figure Checklist

- Clear x/y labels with units or transformations
- Consistent color and shape mapping
- Readable legend or direct labels
- Regression equation or effect summary only when helpful
- Transparent note about filtering rules

## Path Policy

Use placeholders like `<project-root>/data/analysis.csv` and `<project-root>/outputs/figures/`. Resolve real paths from the current workspace or user instructions.

