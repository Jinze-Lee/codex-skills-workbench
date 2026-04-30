from __future__ import annotations

import argparse

import pandas as pd

from harvest_utils import (
    CROSSREF_URL,
    RAW_DIR,
    USER_AGENT,
    clean_text,
    ensure_directories,
    extract_year,
    json_compatible,
    load_config,
    normalize_doi,
    request_json,
    write_csv,
    write_json,
)


def parse_crossref_item(item: dict, query_name: str, search_query: str) -> dict:
    authors = []
    for author in item.get("author", []) or []:
        full_name = " ".join(
            part
            for part in [clean_text(author.get("given")), clean_text(author.get("family"))]
            if part
        )
        if full_name:
            authors.append(full_name)
    links = item.get("link", []) or []
    license_urls = [
        clean_text(entry.get("URL"))
        for entry in item.get("license", []) or []
        if clean_text(entry.get("URL"))
    ]
    pdf_url = ""
    fulltext_url = ""
    for link in links:
        link_url = clean_text(link.get("URL"))
        content_type = clean_text(link.get("content-type")).lower()
        if not pdf_url and "pdf" in content_type:
            pdf_url = link_url
        if not fulltext_url and link_url:
            fulltext_url = link_url
    if not fulltext_url:
        fulltext_url = clean_text((item.get("resource") or {}).get("primary", {}).get("URL"))
    year = None
    for date_key in ["published-print", "published-online", "issued", "created"]:
        parts = ((item.get(date_key) or {}).get("date-parts") or [])
        if parts and parts[0]:
            year = parts[0][0]
            break
    if year is None:
        year = extract_year((item.get("created") or {}).get("date-time"))
    return {
        "query_name": query_name,
        "search_query": search_query,
        "source_database": "crossref",
        "source_record_id": clean_text(item.get("DOI")) or clean_text(item.get("URL")),
        "title": clean_text(" ".join(item.get("title", []) or [])),
        "abstract": clean_text(item.get("abstract")),
        "authors": "; ".join(authors),
        "journal": clean_text(" ".join(item.get("container-title", []) or [])),
        "year": year,
        "doi": normalize_doi(item.get("DOI")),
        "pmid": "",
        "pmcid": "",
        "publication_type": clean_text(item.get("type")),
        "open_access_flag": bool(license_urls or links),
        "fulltext_url": fulltext_url,
        "pdf_url": pdf_url,
        "landing_page_url": clean_text(item.get("URL")),
        "license": "; ".join(license_urls),
        "licenses_json": json_compatible(license_urls),
        "candidate_urls_json": json_compatible(
            [url for url in [pdf_url, fulltext_url, clean_text(item.get("URL"))] if url]
        ),
    }


def search_crossref(config_path: str | None = None) -> pd.DataFrame:
    ensure_directories()
    config = load_config(config_path)
    if not config["sources"].get("crossref", True):
        return pd.DataFrame()

    rows: list[dict] = []
    logs: list[dict] = []
    max_results = int(config["max_results_per_query"].get("crossref", 100))
    page_size = min(int(config["page_size"].get("crossref", 100)), 100)
    delay = float(config["delay_seconds"].get("crossref", 0.5))
    headers = {"User-Agent": f"{USER_AGENT} (mailto:{config.get('email') or 'none@example.com'})"}

    for query in config["queries"]:
        payload = request_json(
            CROSSREF_URL,
            params={
                "query.bibliographic": query["query"],
                "rows": min(max_results, page_size),
            },
            headers=headers,
            delay_seconds=delay,
        )
        write_json(payload, RAW_DIR / f"crossref_search_{query['name']}.json")
        items = payload.get("message", {}).get("items", []) or []
        for item in items[:max_results]:
            rows.append(parse_crossref_item(item, query["name"], query["query"]))
        logs.append(
            {
                "query_name": query["name"],
                "search_query": query["query"],
                "db": "crossref",
                "retrieved_row_count": min(len(items), max_results),
                "reported_total_results": clean_text(payload.get("message", {}).get("total-results")),
            }
        )

    df = pd.DataFrame(rows)
    write_csv(df, RAW_DIR / "crossref_records.csv")
    write_csv(pd.DataFrame(logs), RAW_DIR / "crossref_query_log.csv")
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    search_crossref(args.config)


if __name__ == "__main__":
    main()
