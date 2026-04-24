# Weighted Regression Plot

## Purpose

Generic guide for creating weighted regression plots with gradient color, shape encoding, uncertainty, and interpretable annotations.

This public template removes historical file names and local analysis paths.

## Inputs To Confirm

- Response variable: `<response>`
- Predictor variable: `<predictor>`
- Weight variable: `<weight>`
- Color variable: `<color-variable>`
- Shape/group variable: `<group-variable>`
- Input data: `<input-table>`
- Output directory: `<output-dir>`

## Workflow

1. Validate the meaning and scale of weights.
2. Check missingness and whether zero or negative weights are possible.
3. Fit weighted and, when useful, unweighted comparison models.
4. Plot raw data with weight-aware size or transparency only if it remains readable.
5. Add fitted trend and uncertainty band.
6. Use color and shape for variables that support the interpretation rather than decoration.
7. Export the figure and a model summary table together.

## Interpretation Notes

- Explain what larger weights represent.
- Report whether weighting changes the direction or strength of the relationship.
- Avoid implying causation from a weighted regression unless the study design supports it.

## Generic R Skeleton

```r
model <- lm(response ~ predictor, data = df, weights = weight)
summary(model)
```

