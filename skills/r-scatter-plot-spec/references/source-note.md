# R Scatter Plot Spec

## Purpose

Generic specification for reproducible R scatterplots with regression, grouping, export, and quality control.

This template is public-safe and path-neutral.

## Inputs To Confirm

- Data file: `<input-table>`
- x variable: `<x>`
- y variable: `<y>`
- Optional group/color/shape variables: `<grouping-variables>`
- Model or smoother: linear, polynomial, GAM, LOESS, robust, or none
- Output files: `<figure-file>`, `<stats-file>`

## Workflow

1. Read data with explicit encoding and column-type checks.
2. Validate x/y variables and remove or flag missing values.
3. Check outliers and group sample sizes.
4. Build the plot using a consistent visual mapping.
5. Add model fits and annotations only when they answer the question.
6. Export figure and statistics together.
7. Save session information or package versions for reproducibility.

## R Skeleton

```r
library(ggplot2)

plot <- ggplot(df, aes(x = x_value, y = y_value)) +
  geom_point(alpha = 0.75) +
  geom_smooth(method = 'lm', se = TRUE) +
  theme_classic()

ggsave('<output-dir>/scatter.png', plot, width = 7, height = 5, dpi = 300)
```

