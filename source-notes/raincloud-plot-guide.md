# Raincloud Plot Guide

## Purpose

Generic workflow for raincloud plots that combine distribution, raw observations, and summary statistics.

Use placeholders below and adapt variables, datasets, and paths to the active project context.

## Inputs To Confirm

- Response variable: `<response>`
- Group variable: `<group>`
- Optional facet variable: `<facet>`
- Input table: `<input-table>`
- Output directory: `<output-dir>`
- Desired components: half-eye density, boxplot, jittered points, mean/median markers, intervals

## Workflow

1. Inspect group sizes and missing data.
2. Decide whether values need transformation or normalization.
3. Choose a layout that keeps raw points visible without overplotting.
4. Use distribution layers to show shape, not merely decoration.
5. Add summary markers only when they clarify interpretation.
6. Export a figure with explicit dimensions and DPI.
7. Provide a short note describing the main group differences and uncertainty.

## R Package Options

- `ggdist` for half-eye or slab intervals
- `ggplot2` for points, boxplots, and theme control
- `gghalves` as an alternative half-geometry toolkit

## Generic Export Pattern

```r
ggsave('<output-dir>/raincloud_plot.png', plot, width = 8, height = 5, dpi = 300)
```

