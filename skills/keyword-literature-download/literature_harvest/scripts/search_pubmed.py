from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET

import pandas as pd

from harvest_utils import (
    NCBI_BASE,
    RAW_DIR,
    chunked,
    clean_text,
    ensure_directories,
    extract_year,
    flatten_authors,
    json_compatible,
    load_config,
    normalize_doi,
    normalize_pmcid,
    normalize_pmid,
    request_json,
    request_text,
    write_csv,
    write_json,
)


def article_id_map(article_root: ET.Element) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for node in article_root.findall(".//PubmedData/ArticleIdList/ArticleId"):
        key = clean_text(node.attrib.get("IdType")).lower()
        value = clean_text(node.text)
        if key and value:
            mapping[key] = value
    return mapping


def parse_pubmed_xml(xml_text: str, query_name: str, search_query: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    rows: list[dict] = []
    for article in root.findall(".//PubmedArticle"):
        pmid = clean_text(article.findtext(".//MedlineCitation/PMID"))
        title_node = article.find(".//Article/ArticleTitle")
        title = clean_text(" ".join(title_node.itertext())) if title_node is not None else ""
        abstract_parts = []
        for abstract_node in article.findall(".//Article/Abstract/AbstractText"):
            label = clean_text(abstract_node.attrib.get("Label"))
            text = clean_text(" ".join(abstract_node.itertext()))
            abstract_parts.append(f"{label}: {text}" if label else text)
        authors = []
        for author in article.findall(".//Article/AuthorList/Author"):
            collective = clean_text(author.findtext("CollectiveName"))
            if collective:
                authors.append(collective)
                continue
            last_name = clean_text(author.findtext("LastName"))
            fore_name = clean_text(author.findtext("ForeName"))
            full_name = " ".join(part for part in [fore_name, last_name] if part)
            if full_name:
                authors.append(full_name)
        journal = clean_text(article.findtext(".//Article/Journal/Title"))
        pubdate_text = " ".join(
            clean_text(node.text)
            for node in article.findall(".//Article/Journal/JournalIssue/PubDate/*")
            if clean_text(node.text)
        )
        if not pubdate_text:
            pubdate_text = clean_text(article.findtext(".//Article/Journal/JournalIssue/PubDate/MedlineDate"))
        ids = article_id_map(article)
        publication_types = [
            clean_text(node.text)
            for node in article.findall(".//Article/PublicationTypeList/PublicationType")
            if clean_text(node.text)
        ]
        pmcid = normalize_pmcid(ids.get("pmc") or ids.get("pmcid"))
        doi = normalize_doi(ids.get("doi"))
        rows.append(
            {
                "query_name": query_name,
                "search_query": search_query,
                "source_database": "pubmed",
                "source_record_id": pmid,
                "title": title,
                "abstract": " ".join(part for part in abstract_parts if part).strip(),
                "authors": flatten_authors(authors),
                "journal": journal,
                "year": extract_year(pubdate_text),
                "doi": doi,
                "pmid": normalize_pmid(pmid),
                "pmcid": pmcid,
                "publication_type": "; ".join(publication_types),
                "open_access_flag": bool(pmcid),
                "fulltext_url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else "",
                "pdf_url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/" if pmcid else "",
                "landing_page_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                "license": "",
                "licenses_json": json_compatible([]),
                "candidate_urls_json": json_compatible(
                    [
                        url
                        for url in [
                            f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else "",
                            f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/" if pmcid else "",
                        ]
                        if url
                    ]
                ),
            }
        )
    return rows


def parse_pmc_summary(summary_json: dict, query_name: str, search_query: str) -> list[dict]:
    rows: list[dict] = []
    for uid in summary_json.get("result", {}).get("uids", []):
        record = summary_json["result"].get(uid, {})
        article_ids = {
            clean_text(item.get("idtype")).lower(): clean_text(item.get("value"))
            for item in record.get("articleids", [])
        }
        pmcid = normalize_pmcid(article_ids.get("pmcid") or uid)
        pmid = normalize_pmid(article_ids.get("pmid"))
        doi = normalize_doi(article_ids.get("doi"))
        authors = [item.get("name") for item in record.get("authors", [])]
        rows.append(
            {
                "query_name": query_name,
                "search_query": search_query,
                "source_database": "pmc",
                "source_record_id": pmcid or clean_text(uid),
                "title": clean_text(record.get("title")),
                "abstract": "",
                "authors": flatten_authors(authors),
                "journal": clean_text(record.get("fulljournalname")),
                "year": extract_year(record.get("pubdate")),
                "doi": doi,
                "pmid": pmid,
                "pmcid": pmcid,
                "publication_type": "",
                "open_access_flag": bool(pmcid),
                "fulltext_url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else "",
                "pdf_url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/" if pmcid else "",
                "landing_page_url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else "",
                "license": "",
                "licenses_json": json_compatible([]),
                "candidate_urls_json": json_compatible(
                    [
                        url
                        for url in [
                            f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else "",
                            f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/" if pmcid else "",
                        ]
                        if url
                    ]
                ),
            }
        )
    return rows


def search_pubmed_and_pmc(config_path: str | None = None) -> pd.DataFrame:
    ensure_directories()
    config = load_config(config_path)
    queries = config["queries"]
    max_results = config["max_results_per_query"]
    delays = config["delay_seconds"]
    tool_name = config.get("tool_name", "keyword_research_harvest")
    email = config.get("email", "")

    rows: list[dict] = []
    logs: list[dict] = []

    if config["sources"].get("pubmed", True):
        for query in queries:
            esearch_json = request_json(
                f"{NCBI_BASE}/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": query["query"],
                    "retmax": max_results.get("pubmed", 100),
                    "retmode": "json",
                    "tool": tool_name,
                    "email": email,
                },
                delay_seconds=delays.get("pubmed", 0.34),
            )
            write_json(esearch_json, RAW_DIR / f"pubmed_esearch_{query['name']}.json")
            id_list = esearch_json.get("esearchresult", {}).get("idlist", [])
            logs.append(
                {
                    "query_name": query["name"],
                    "search_query": query["query"],
                    "db": "pubmed",
                    "retrieved_id_count": len(id_list),
                }
            )
            for chunk in chunked(id_list, 100):
                xml_text = request_text(
                    f"{NCBI_BASE}/efetch.fcgi",
                    params={
                        "db": "pubmed",
                        "id": ",".join(chunk),
                        "retmode": "xml",
                        "tool": tool_name,
                        "email": email,
                    },
                    delay_seconds=delays.get("pubmed", 0.34),
                )
                rows.extend(parse_pubmed_xml(xml_text, query["name"], query["query"]))

    if config["sources"].get("pmc", True):
        for query in queries:
            esearch_json = request_json(
                f"{NCBI_BASE}/esearch.fcgi",
                params={
                    "db": "pmc",
                    "term": query["query"],
                    "retmax": max_results.get("pmc", 100),
                    "retmode": "json",
                    "tool": tool_name,
                    "email": email,
                },
                delay_seconds=delays.get("pmc", 0.34),
            )
            write_json(esearch_json, RAW_DIR / f"pmc_esearch_{query['name']}.json")
            id_list = esearch_json.get("esearchresult", {}).get("idlist", [])
            logs.append(
                {
                    "query_name": query["name"],
                    "search_query": query["query"],
                    "db": "pmc",
                    "retrieved_id_count": len(id_list),
                }
            )
            for chunk in chunked(id_list, 200):
                summary_json = request_json(
                    f"{NCBI_BASE}/esummary.fcgi",
                    params={
                        "db": "pmc",
                        "id": ",".join(chunk),
                        "retmode": "json",
                        "tool": tool_name,
                        "email": email,
                    },
                    delay_seconds=delays.get("pmc", 0.34),
                )
                rows.extend(parse_pmc_summary(summary_json, query["name"], query["query"]))

    df = pd.DataFrame(rows)
    write_csv(df, RAW_DIR / "pubmed_pmc_records.csv")
    write_csv(pd.DataFrame(logs), RAW_DIR / "pubmed_pmc_query_log.csv")
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    search_pubmed_and_pmc(args.config)


if __name__ == "__main__":
    main()
