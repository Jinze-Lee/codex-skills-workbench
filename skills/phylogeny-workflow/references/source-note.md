# Phylogeny Workflow

## Purpose

Generic workflow for phylogenetic tree handling, trait mapping, and comparative analysis.

Use placeholders below and adapt tree files, metadata, and taxon lists to the active project context.

## Inputs To Confirm

- Tree file: `<tree-file>`
- Trait or metadata table: `<trait-table>`
- Taxon key column: `<taxon-column>`
- Analysis goal: visualization, pruning, matching, phylogenetic signal, comparative model, or ancestral reconstruction
- Output directory: `<output-dir>`

## Workflow

1. Read and validate the tree format.
2. Standardize taxon names in both tree and metadata.
3. Report taxa present only in the tree or only in the metadata.
4. Prune or match data according to explicit rules.
5. Run the selected tree visualization or comparative method.
6. Export matched data, pruned tree, figures, and method parameters.
7. Interpret results with attention to tree uncertainty and sampling coverage.

## Output Checklist

- Taxon matching report
- Pruned or matched tree
- Matched trait table
- Figure or analysis result table
- Reproducibility log

## Path Policy

Use placeholders such as `<project-root>/data/tree.nwk` and `<project-root>/outputs/phylogeny/`. Replace them only with paths supplied by the current task.

