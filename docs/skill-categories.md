# Skill Categories

The `skills/` directory is intentionally flat because Codex installations normally expect each skill package to be a direct child of the skills root. To make the repository easier to browse, this project groups skills through `manifests/skills.json` and this document.

## Environment And Operations

Use these skills when the main question is about running commands, choosing runtimes, or moving a workflow into a new project.

| Skill | Invocation | Use when |
| --- | --- | --- |
| Shell Choice Guide | `$shell-choice-guide` | Choose the safest shell for Windows, Git, R/Python, file operations, or desktop automation tasks. |
| R Python Runtime Guide | `$r-python-runtime-guide` | Discover and invoke R/Python runtimes without hard-coding machine-specific paths. |
| Method Transfer Guide | `$method-transfer-guide` | Move an analysis method, plotting pattern, or automation workflow into a new project safely. |

## Presentation And Reporting

Use these skills when the main output is a deck, report, or literature synthesis.

| Skill | Invocation | Use when |
| --- | --- | --- |
| PPT Production Guide | `$ppt-production-guide` | Build PowerPoint decks, custom image walls, report slides, and ask whether to show visible PowerPoint COM generation. |
| Literature Synthesis | `$literature-synthesis-guide` | Summarize papers into evidence tables, thematic synthesis, or citation-ready narrative notes. |

## Research And Literature

Use these skills when the main task is discovering, harvesting, downloading, or organizing scholarly literature.

| Skill | Invocation | Use when |
| --- | --- | --- |
| Keyword Literature Download | `$keyword-literature-download` | Search scholarly APIs for keyword topics, download legally accessible PDFs, cache non-PDF helper files separately, and deduplicate results. |

## Plotting And Visualization

Use these skills when the main output is a figure or a figure-production decision.

| Skill | Invocation | Use when |
| --- | --- | --- |
| Plotting Tool Selection | `$plotting-tool-selection` | Decide whether a figure should be made with R, Python, PowerPoint, vector tools, or spreadsheets. |
| ggplot2 Richtext Fixes | `$ggplot2-richtext-fixes` | Fix ggplot2 labels, superscripts, subscripts, Markdown/HTML labels, or export rendering issues. |
| R Scatter Plot Spec | `$r-scatter-plot-spec` | Create reproducible R scatterplots with regression, grouping, export, and statistics. |
| Trait Environment Scatterplots | `$trait-environment-scatterplots` | Create trait-environment or response-predictor scatterplots with grouping and model interpretation. |
| Significance Group Scatter | `$significance-group-scatter` | Emphasize statistically supported groups in grouped scatterplots while preserving context. |
| Raincloud Plot Guide | `$raincloud-plot-guide` | Build raincloud plots that combine distributions, raw points, intervals, and summary markers. |
| Weighted Regression Plot | `$weighted-regression-plot` | Create weighted regression plots with interpretable weights, uncertainty, and visual encodings. |

## Data Processing And Modeling

Use these skills when the main task is a multi-step analysis pipeline rather than a single plot.

| Skill | Invocation | Use when |
| --- | --- | --- |
| Weighted Data Pipeline | `$weighted-data-pipeline` | Run an end-to-end weighted data workflow from cleaning and merging through models and figures. |

## Ecology And Evolution

Use these skills for domain-specific ecological or evolutionary workflows.

| Skill | Invocation | Use when |
| --- | --- | --- |
| Hypervolume Workflow | `$hypervolume-workflow` | Analyze ecological niche, trait-space, hypervolume, overlap, or centroid-distance questions. |
| Phylogeny Workflow | `$phylogeny-workflow` | Match trait data to phylogenetic trees, prune trees, visualize trees, or run comparative analyses. |
