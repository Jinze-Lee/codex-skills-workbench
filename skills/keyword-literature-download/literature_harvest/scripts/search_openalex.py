from __future__ import annotations

import argparse

import pandas as pd

from harvest_utils import (
    OPENALEX_URL,
    RAW_DIR,
    USER_AGENT,
    clean_text,
    ensure_directories,
    json_compatible,
    load_config,
    normalize_doi,
    normalize_pmid,
    reconstruct_openalex_abstract,
    request_json,
    write_csv,
    write_json,
)


def parse_openalex_item(item: dict, query_name: str, search_query: str) -> dict:
    authors = [
        clean_text((authorship.get("author") or {}).get("display_name"))
        for authorship in item.get("authorships", []) or []
        if clean_text((authorship.get("author") or {}).get("display_name"))
    ]
    open_access = item.get("open_access", {}) or {}
    best_oa_location = item.get("best_oa_location") or {}
    primary_location = item.get("primary_location") or {}
    ids = item.get("ids") or {}
    doi = normalize_doi(item.get("doi") or ids.get("doi"))
    pmid = normalize_pmid(ids.get("pmid"))
    oa_url = (
        clean_text(open_access.get("oa_url"))
        or clean_text(best_oa_location.get("pdf_url"))
        or clean_text(best_oa_location.get("landing_page_url"))
        or clean_text(primary_location.get("landing_page_url"))
    )
    pdf_url = clean_text(best_oa_location.get("pdf_url"))
    license_text = clean_text(best_oa_location.get("license")) or clean_text(
        primary_location.get("license")
    )
    journal = clean_text((primary_location.get("source") or {}).get("display_name"))
    return {
        "query_name": query_name,
        "search_query": search_query,
        "source_database": "openalex",
        "source_record_id": clean_text(item.get("id")),
        "title": clean_text(item.get("title")),
        "abstract": reconstruct_openalex_abstract(item.get("abstract_inverted_index")),
        "authors": "; ".join(authors),
        "journal": journal,
        "year": item.get("publication_year"),
        "doi": doi,
        "pmid": pmid,
        "pmcid": "",
        "publication_type": clean_text(item.get("type")),
        "open_access_flag": bool(open_access.get("is_oa")),
        "fulltext_url": oa_url,
        "pdf_url": pdf_url,
        "landing_page_url": clean_text(item.get("id")),
        "license": license_text,
        "licenses_json": json_compatible([license_text] if license_text else []),
        "candidate_urls_json": json_compatible([url for url in [pdf_url, oa_url] if url]),
    }


def search_openalex(config_path: str | None = None) -> pd.DataFrame:
    ensure_directories()
    config = load_config(config_path)
    if not config["sources"].get("openalex", True):
        return pd.DataFrame()

    rows: list[dict] = []
    logs: list[dict] = []
    max_results = int(config["max_results_per_query"].get("openalex", 100))
    page_size = min(int(config["page_size"].get("openalex", 100)), 200)
    delay = float(config["delay_seconds"].get("openalex", 0.34))

    for query in config["queries"]:
        retrieved = 0
        page = 1
        first_payload = None
        while retrieved < max_results:
            payload = request_json(
                OPENALEX_URL,
                params={
                    "search": query["query"],
                    "per-page": min(page_size, max_results - retrieved),
                    "page": page,
                },
                headers={"User-Agent": USER_AGENT},
                delay_seconds=delay,
            )
            if first_payload is None:
                first_payload = payload
            items = payload.get("results", []) or []
            if not items:
                break
            for item in items:
                rows.append(parse_openalex_item(item, query["name"], query["query"]))
                retrieved += 1
                if retrieved >= max_results:
                    break
            if len(items) < page_size:
                break
            page += 1
        logs.append(
            {
                "query_name": query["name"],
                "search_query": query["query"],
                "db": "openalex",
                "retrieved_row_count": retrieved,
                "reported_total_results": (first_payload or {}).get("meta", {}).get("count", 0),
            }
        )
        if first_payload is not None:
            write_json(first_payload, RAW_DIR / f"openalex_search_{query['name']}.json")

    df = pd.DataFrame(rows)
    write_csv(df, RAW_DIR / "openalex_records.csv")
    write_csv(pd.DataFrame(logs), RAW_DIR / "openalex_query_log.csv")
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    search_openalex(args.config)


if __name__ == "__main__":
    main()
