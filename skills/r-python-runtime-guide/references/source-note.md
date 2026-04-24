# R Python Runtime Guide

## Purpose

Generic guidance for choosing and invoking R and Python runtimes in reproducible analysis projects.

Use placeholders below and discover runtimes from the active project context.

## Inputs To Confirm

- Operating system and shell
- Project root: `<project-root>`
- R executable or `Rscript` path, if non-standard
- Python executable or virtual environment, if non-standard
- Package manager: `renv`, `pak`, `pip`, `uv`, `conda`, or project-specific tooling

## Runtime Discovery

PowerShell examples:

```powershell
Get-Command Rscript -ErrorAction SilentlyContinue
Get-Command python -ErrorAction SilentlyContinue
Get-Command uv -ErrorAction SilentlyContinue
```

R examples:

```r
R.version.string
.libPaths()
sessionInfo()
```

Python examples:

```powershell
python --version
python -m pip --version
python -c "import sys; print(sys.executable)"
```

## Invocation Patterns

R:

```powershell
& '<path-to-Rscript>' '<project-root>/scripts/analysis.R' --input '<input-file>' --output '<output-dir>'
```

Python:

```powershell
& '<path-to-python>' '<project-root>/scripts/analysis.py' --input '<input-file>' --output '<output-dir>'
```

## Reproducibility Notes

- Prefer project-local environments when available.
- Log interpreter paths and package versions in outputs.
- Do not hard-code user-specific library directories in reusable scripts.

