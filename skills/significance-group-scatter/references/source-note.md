# Significance Group Scatter

## Purpose

Generic guide for grouped scatterplots that emphasize statistically supported relationships while preserving context for non-significant groups.

This public template removes local scripts, paths, and project-specific trait names.

## Inputs To Confirm

- Response variable: `<response>`
- Predictor variable: `<predictor>`
- Group variable: `<group>`
- Statistical model: linear model, mixed model, robust regression, correlation, or other method
- Significance criterion: p-value, confidence interval, false-discovery adjustment, or model comparison
- Output directory: `<output-dir>`

## Workflow

1. Fit the chosen model separately by group or with interaction terms, depending on the hypothesis.
2. Export a statistics table with effect size, uncertainty, p-value or interval, and sample size.
3. Plot all groups for context.
4. Visually emphasize significant or supported groups using line weight, opacity, labels, or color.
5. Keep non-significant groups visible but visually quieter.
6. State the criterion used for emphasis in the caption or accompanying notes.

## Interpretation Notes

- Significance emphasis is a communication device, not a substitute for model diagnostics.
- Report effect size and uncertainty alongside significance.
- Avoid hiding non-significant groups if they are needed for context.

