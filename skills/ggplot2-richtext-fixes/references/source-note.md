# ggplot2 Richtext Fixes

## Purpose

Generic guidance for fixing superscripts, subscripts, special symbols, and rich text rendering issues in `ggplot2` figures.

Use placeholders below and confirm fonts, devices, and paths in the active project context.

## Inputs To Confirm

- Plotting system: base `ggplot2`, `ggtext`, `gridtext`, `patchwork`, or export device
- Target text elements: axis labels, legend labels, facet strips, annotations, or captions
- Required notation: superscript, subscript, italic species names, units, math expressions, or HTML/Markdown labels
- Export format: PNG, TIFF, PDF, SVG, PPT-ready image

## Workflow

1. Identify whether the label should use plotmath syntax, Markdown/HTML, or plain Unicode.
2. For plotmath labels, use `expression()` or `bquote()` and keep labels as expressions.
3. For Markdown/HTML labels, use `ggtext::element_markdown()` or `ggtext::geom_richtext()`.
4. Keep label mapping separate from data transformation.
5. Test the export device because RStudio preview and saved files can render differently.
6. Export a small diagnostic figure before batch rendering many plots.

## Generic Examples

Plotmath:

```r
ggplot(df, aes(x, y)) +
  geom_point() +
  labs(y = expression(pH[soil]), x = expression(CO[2]))
```

Markdown label:

```r
ggplot(df, aes(x, y)) +
  geom_point() +
  labs(y = 'Soil pH<sub>mean</sub>') +
  theme(axis.title.y = ggtext::element_markdown())
```

## Export Notes

- Prefer explicit `width`, `height`, `dpi`, and device settings.
- Use project fonts only after confirming they exist on the current machine.
- Keep fallbacks for headless or server environments.

