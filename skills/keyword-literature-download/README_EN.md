# Keyword Literature Download Skill

This Codex skill searches scholarly APIs for any keyword set, builds candidate literature tables, downloads legally accessible PDFs, caches non-PDF helper files separately, and deduplicates the final PDF collection.

It uses public metadata and full-text links from PubMed/PMC, Europe PMC, Crossref, and OpenAlex. It does not bypass paywalls or save HTML/XML files as PDFs.

## Quick Start

1. Copy the config template:

```powershell
Copy-Item .\references\config_template.json .\my_topic_config.json
```

2. Edit `my_topic_config.json`, especially:

- `queries`
- `include_terms`
- `secondary_terms`
- `exclude_terms`

3. Start a new run:

```powershell
python .\scripts\run_keyword_harvest_no_dedup.py `
  --output-root ".\runs" `
  --config ".\my_topic_config.json" `
  --run-name "my_topic_001" `
  --pdf-output-dir ".\pdfs\my_topic" `
  --download-workers 8
```

4. Resume downloads, chase PDF links from cached HTML, and deduplicate:

```powershell
python .\scripts\continue_download_and_dedup.py `
  --run-root ".\runs\my_topic_001" `
  --retry-failed
```

## Main Outputs

- `keyword_research_candidate_table.csv`: full candidate metadata.
- `keyword_research_high_priority.csv`: higher-relevance candidate records.
- `keyword_research_medium_priority.csv`: medium-relevance candidate records.
- `download_logs/keyword_research_download_log.csv`: primary download status log.
- `download_logs/keyword_research_html_second_pass.csv`: HTML-to-PDF second-pass log.
- `download_work/non_pdf_payloads/`: auxiliary HTML/XML cache.
- `keyword_research_dedup_manifest.csv`: PDF deduplication manifest.
- `downloaded_pdfs_deduplicated/`: deduplicated PDF-only folder.

## Requirements

- Python 3.10 or newer.
- `pandas`.
- Network access to the scholarly APIs and openly accessible publisher pages.

Install the Python dependency if needed:

```powershell
python -m pip install pandas
```

## Compliance

This skill only downloads files that are legally accessible in the current network environment. Paywalled or inaccessible records remain in the metadata and logs instead of being silently discarded.
