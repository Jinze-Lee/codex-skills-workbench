---
name: keyword-literature-download
description: Use when the user wants a reusable local workflow to search scholarly APIs for topic keywords, build a candidate table, rapidly download accessible PDFs into a PDF-only folder, optionally cache HTML/XML outside that folder for second-pass PDF discovery, and deduplicate the PDF files.
---

# Keyword Research Harvest

Use this skill when the user gives a topic or keyword set and wants a local literature-harvesting workflow, not a one-off manual search.

## What this skill does

- Bundles its own `literature_harvest/scripts` stack, including `search_pubmed.py`, `search_europepmc.py`, `search_crossref.py`, `search_openalex.py`, `merge_and_deduplicate.py`, `download_fulltexts.py`, and `harvest_utils.py`.
- Searches PubMed/PMC, Europe PMC, Crossref, and OpenAlex through the bundled pipeline.
- Builds a no-dedup candidate table first.
- Downloads legal PDFs in parallel for faster collection.
- Lets the user specify the PDF output folder with `--pdf-output-dir` or `download.pdf_output_dir`.
- Keeps the PDF output folder PDF-only; HTML/XML helper files are cached under `download_work/non_pdf_payloads/`.
- Runs a second pass to chase PDF links from saved HTML pages.
- Produces a PDF-only deduplicated file folder and manifest after downloading.

## Dependency model

This skill is self-contained. The target project does not need to already contain:

- `literature_harvest/`
- `search_pubmed.py`
- `download_fulltexts.py`

The bundled copies live under:

- `literature_harvest/scripts/`

## Files in this skill

- `scripts/run_keyword_harvest_no_dedup.py`
  Use this to launch a new broad keyword harvest run into a new run folder.
- `scripts/continue_download_and_dedup.py`
  Use this to resume pending downloads, try HTML-to-PDF second pass, and build a deduplicated download set.
- `literature_harvest/scripts/`
  Bundled search and download dependencies copied from a working local harvest stack so the skill is portable.
- `references/config_template.json`
  Copy and edit this for the topic-specific query set and filtering terms.
- `references/prompt_template.md`
  Reusable prompt for another AI/agent.

## Recommended workflow

1. Choose any output parent folder where the new harvest run folder should be created.
2. Copy `references/config_template.json` and edit it for the user's topic keywords.
3. Run `scripts/run_keyword_harvest_no_dedup.py` with:
   - `--output-root`
   - `--config`
   - `--run-name`
   - optional `--pdf-output-dir <folder>` to put generated PDFs in a specific PDF-only folder
   - optional `--download-workers <N>` to tune parallel downloads
4. If the job is large, rerun with the same `--run-name` and `--skip-search` to avoid repeating API search.
5. Run `scripts/continue_download_and_dedup.py --run-root <run-folder> --retry-failed`; it reuses the stored PDF folder unless `--pdf-output-dir` is supplied again.
6. Report:
   - candidate count
   - PDF downloaded count
   - true PDF count
   - HTML/XML cache count
   - remaining pending
   - deduplicated keep count

## Constraints

- Do not silently drop failed downloads.
- Keep metadata even when download fails.
- Prefer original research when the config asks for it, but do not hard-code one research domain.
- Do not claim HTML/XML is PDF.
- Never write HTML, XML, CSV, logs, manifests, or other helper files into the PDF output folder.
- Verify a file starts with the PDF signature before saving it into the PDF output folder.
- Treat second-pass cluster-like or support-like annotations as auxiliary only; downloading remains the primary task.

## When to read references

- Read `references/config_template.json` before preparing a new run config.
- Read `references/prompt_template.md` when the user wants to hand this skill to another AI/agent.
