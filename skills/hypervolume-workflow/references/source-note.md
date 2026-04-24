# Hypervolume Workflow

## Purpose

Generic workflow guidance for ecological niche, trait-space, or hypervolume analyses.

Use placeholders below and adapt variables, groups, and taxa to the active project context.

## Inputs To Confirm

- Analysis unit: species, populations, sites, treatments, or groups
- Trait or environmental variables: `<variable-list>`
- Grouping columns: `<group-columns>`
- Input data: `<input-table>`
- Output directory: `<output-dir>`
- Method choice: kernel hypervolume, convex hull, PCA/ordination space, or alternative niche metric

## Workflow

1. Inspect the data structure, missingness, units, and group sample sizes.
2. Standardize or transform variables only when scientifically justified.
3. Check whether groups have enough observations for the chosen hypervolume method.
4. Build the niche or trait space using reproducible parameters.
5. Compare volume, overlap, centroid distance, and uncertainty across groups.
6. Export tables, figures, parameters, and session information.
7. Interpret results in terms of the study design rather than treating volume as automatically better or worse.

## Output Checklist

- Cleaned analysis table
- Parameter log
- Hypervolume or niche metric summary
- Overlap or distance matrix
- Diagnostic plots
- Main result figures
- Reproducibility notes

## Path Policy

Use placeholders such as `<project-root>/data/input.csv` and `<project-root>/outputs/hypervolume/`. Replace them with user-provided paths at runtime.

