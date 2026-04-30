from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from harvest_utils import (
    MERGED_DIR,
    RAW_DIR,
    clean_text,
    ensure_directories,
    merge_source_rows,
    normalize_doi,
    normalize_pmcid,
    normalize_pmid,
    normalize_title,
    write_csv,
    write_markdown,
)


SOURCE_FILES = [
    "pubmed_pmc_records.csv",
    "europepmc_records.csv",
    "crossref_records.csv",
    "openalex_records.csv",
]


def load_sources() -> tuple[pd.DataFrame, list[dict]]:
    frames = []
    source_stats: list[dict] = []
    for filename in SOURCE_FILES:
        path = RAW_DIR / filename
        if not path.exists():
            source_stats.append(
                {
                    "source_file": filename,
                    "exists": False,
                    "raw_rows": 0,
                }
            )
            continue
        df = pd.read_csv(path)
        df["source_file"] = filename
        frames.append(df)
        source_stats.append(
            {
                "source_file": filename,
                "exists": True,
                "raw_rows": int(len(df)),
            }
        )
    if not frames:
        return pd.DataFrame(), source_stats
    merged = pd.concat(frames, ignore_index=True)
    return merged, source_stats


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    for column in [
        "query_name",
        "search_query",
        "source_database",
        "source_record_id",
        "title",
        "abstract",
        "authors",
        "journal",
        "publication_type",
        "fulltext_url",
        "pdf_url",
        "landing_page_url",
        "license",
        "licenses_json",
        "candidate_urls_json",
    ]:
        if column not in data.columns:
            data[column] = ""
        data[column] = data[column].map(clean_text)
    if "year" not in data.columns:
        data["year"] = pd.NA
    data["year"] = pd.to_numeric(data["year"], errors="coerce").astype("Int64")
    data["doi"] = data.get("doi", "").map(normalize_doi)
    data["pmid"] = data.get("pmid", "").map(normalize_pmid)
    data["pmcid"] = data.get("pmcid", "").map(normalize_pmcid)
    data["open_access_flag"] = (
        data.get("open_access_flag", False)
        .map(lambda value: str(value).strip().lower() in {"1", "true", "yes", "y"})
        .astype(bool)
    )
    data["title_normalized"] = data["title"].map(normalize_title)
    return data


def deduplicate(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    data = df.copy()
    data["dedup_group_key"] = ""
    data["dedup_rule"] = ""

    doi_mask = data["doi"].str.len() > 0
    data.loc[doi_mask, "dedup_group_key"] = "doi:" + data.loc[doi_mask, "doi"]
    data.loc[doi_mask, "dedup_rule"] = "doi_exact"

    no_key_mask = data["dedup_group_key"].eq("")
    pmid_mask = no_key_mask & data["pmid"].str.len().gt(0)
    data.loc[pmid_mask, "dedup_group_key"] = "pmid:" + data.loc[pmid_mask, "pmid"]
    data.loc[pmid_mask, "dedup_rule"] = "pmid_exact"

    no_key_mask = data["dedup_group_key"].eq("")
    pmcid_mask = no_key_mask & data["pmcid"].str.len().gt(0)
    data.loc[pmcid_mask, "dedup_group_key"] = "pmcid:" + data.loc[pmcid_mask, "pmcid"]
    data.loc[pmcid_mask, "dedup_rule"] = "pmcid_exact"

    no_key_mask = data["dedup_group_key"].eq("")
    title_mask = no_key_mask & data["title_normalized"].str.len().gt(0)
    data.loc[title_mask, "dedup_group_key"] = "title:" + data.loc[title_mask, "title_normalized"]
    data.loc[title_mask, "dedup_rule"] = "normalized_title"

    no_key_mask = data["dedup_group_key"].eq("")
    data.loc[no_key_mask, "dedup_group_key"] = (
        "row:" + data.loc[no_key_mask].index.astype(str)
    )
    data.loc[no_key_mask, "dedup_rule"] = "no_key_fallback"

    dedup_rows = []
    for _, group in data.groupby("dedup_group_key", sort=False):
        dedup_rows.append(merge_source_rows(group))
    dedup_df = pd.DataFrame(dedup_rows)

    stats = {
        "raw_rows": int(len(data)),
        "deduplicated_rows": int(len(dedup_df)),
        "removed_as_duplicates": int(len(data) - len(dedup_df)),
        "rule_counts": data["dedup_rule"].value_counts(dropna=False).to_dict(),
        "multi_source_groups": int((dedup_df["matched_sources_count"] > 1).sum()),
    }
    return dedup_df, stats


def dedup_report(source_stats: list[dict], stats: dict) -> str:
    lines = [
        "# Deduplication Report",
        "",
        "## Source Inputs",
        "",
    ]
    for row in source_stats:
        lines.append(
            f"- `{row['source_file']}`: exists `{row['exists']}`, rows `{row['raw_rows']}`."
        )
    lines.extend(
        [
            "",
            "## Overall Counts",
            "",
            f"- Raw merged rows: `{stats['raw_rows']}`",
            f"- Rows after deduplication: `{stats['deduplicated_rows']}`",
            f"- Removed duplicate rows: `{stats['removed_as_duplicates']}`",
            f"- Multi-source merged groups: `{stats['multi_source_groups']}`",
            "",
            "## Key Assignment Rules",
            "",
            f"- Rule counts: `{stats['rule_counts']}`",
            "- Priority order: DOI exact -> PMID exact -> PMCID exact -> normalized title -> row fallback.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    _ = parser.parse_args()

    ensure_directories()
    merged_raw, source_stats = load_sources()
    if merged_raw.empty:
        empty = pd.DataFrame()
        write_csv(empty, MERGED_DIR / "keyword_research_search_results_raw.csv")
        write_csv(empty, MERGED_DIR / "keyword_research_search_results_deduplicated.csv")
        write_markdown(
            "# Deduplication Report\n\nNo source metadata files were found.\n",
            MERGED_DIR.parent / "reports" / "deduplication_report.md",
        )
        return

    merged_raw = normalize_columns(merged_raw)
    write_csv(merged_raw, MERGED_DIR / "keyword_research_search_results_raw.csv")
    dedup_df, stats = deduplicate(merged_raw)
    write_csv(dedup_df, MERGED_DIR / "keyword_research_search_results_deduplicated.csv")
    write_markdown(
        dedup_report(source_stats, stats),
        MERGED_DIR.parent / "reports" / "deduplication_report.md",
    )


if __name__ == "__main__":
    main()
