from __future__ import annotations

import csv
import html
import json
import os
import re
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
HARVEST_DIR = (
    Path(os.environ["KEYWORD_HARVEST_ROOT"]).resolve()
    if os.environ.get("KEYWORD_HARVEST_ROOT")
    else SCRIPT_DIR.parent
)
RAW_DIR = HARVEST_DIR / "raw_api_results"
MERGED_DIR = HARVEST_DIR / "merged_tables"
PDF_DIR = HARVEST_DIR / "downloaded_pdfs"
LOG_DIR = HARVEST_DIR / "download_logs"
REPORT_DIR = HARVEST_DIR / "reports"
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "config_search_terms.yaml"
USER_AGENT = "keyword-research-harvest/0.1"
REQUEST_TIMEOUT = 45

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EUROPEPMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPEPMC_FULLTEXT_XML = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
CROSSREF_URL = "https://api.crossref.org/works"
OPENALEX_URL = "https://api.openalex.org/works"


def ensure_directories() -> None:
    for path in [RAW_DIR, MERGED_DIR, PDF_DIR, LOG_DIR, REPORT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(data: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_markdown(text: str, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def json_compatible(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_text(value: Any) -> str:
    return clean_text(value).lower()


def normalize_title(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_doi(value: Any) -> str:
    text = normalize_text(value)
    text = text.replace("https://doi.org/", "").replace("http://doi.org/", "")
    text = text.replace("doi:", "").strip().rstrip(".")
    return text


def normalize_pmid(value: Any) -> str:
    return re.sub(r"\D+", "", clean_text(value))


def normalize_pmcid(value: Any) -> str:
    text = clean_text(value).upper().replace("PMC", "")
    digits = re.sub(r"\D+", "", text)
    return f"PMC{digits}" if digits else ""


def extract_year(value: Any) -> int | None:
    text = clean_text(value)
    match = re.search(r"(19|20)\d{2}", text)
    return int(match.group(0)) if match else None


def chunked(items: list[Any], size: int) -> Iterable[list[Any]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def request_json(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    delay_seconds: float = 0.34,
    retries: int = 3,
) -> Any:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers=request_headers)
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT, context=ssl.create_default_context()) as response:
                payload = json.load(response)
            time.sleep(delay_seconds)
            return payload
        except Exception as exc:
            last_error = exc
            time.sleep(delay_seconds * attempt)
    raise RuntimeError(f"Failed request_json for {url}: {last_error}")


def request_text(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    delay_seconds: float = 0.34,
    retries: int = 3,
) -> str:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers=request_headers)
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT, context=ssl.create_default_context()) as response:
                payload = response.read().decode("utf-8", errors="replace")
            time.sleep(delay_seconds)
            return payload
        except Exception as exc:
            last_error = exc
            time.sleep(delay_seconds * attempt)
    raise RuntimeError(f"Failed request_text for {url}: {last_error}")


def flatten_authors(author_items: Iterable[Any]) -> str:
    names: list[str] = []
    for author in author_items or []:
        if isinstance(author, str):
            author_name = clean_text(author)
        elif isinstance(author, dict):
            author_name = clean_text(
                author.get("name")
                or author.get("fullName")
                or author.get("display_name")
                or " ".join(
                    part
                    for part in [clean_text(author.get("given")), clean_text(author.get("family"))]
                    if part
                )
            )
        else:
            author_name = clean_text(author)
        if author_name:
            names.append(author_name)
    return "; ".join(dict.fromkeys(names))


def reconstruct_openalex_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    positions: dict[int, str] = {}
    for token, values in inverted_index.items():
        for position in values:
            positions[position] = token
    return clean_text(" ".join(positions[index] for index in sorted(positions)))


def source_priority(source_name: str) -> int:
    order = {"pubmed": 5, "pmc": 4, "europepmc": 3, "crossref": 2, "openalex": 1}
    return order.get(source_name, 0)


def record_richness_score(row: pd.Series | dict[str, Any]) -> tuple[int, int]:
    data = row if isinstance(row, dict) else row.to_dict()
    completeness = 0
    for column in [
        "title",
        "abstract",
        "authors",
        "journal",
        "year",
        "doi",
        "pmid",
        "pmcid",
        "license",
        "fulltext_url",
        "pdf_url",
    ]:
        if clean_text(data.get(column)):
            completeness += 1
    return completeness, source_priority(clean_text(data.get("source_database")))


def combine_unique(values: Iterable[Any], separator: str = "; ") -> str:
    cleaned = [clean_text(value) for value in values if clean_text(value)]
    unique = list(dict.fromkeys(cleaned))
    return separator.join(unique)


def combine_json_lists(values: Iterable[Any]) -> str:
    merged: list[Any] = []
    seen: set[str] = set()
    for value in values:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        if isinstance(value, str):
            text = value.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
                items = parsed if isinstance(parsed, list) else [parsed]
            except json.JSONDecodeError:
                items = [text]
        elif isinstance(value, list):
            items = value
        else:
            items = [value]
        for item in items:
            marker = json.dumps(item, ensure_ascii=False, sort_keys=True)
            if marker not in seen:
                seen.add(marker)
                merged.append(item)
    return json.dumps(merged, ensure_ascii=False)


def pick_first_url(values: Iterable[Any]) -> str:
    for value in values:
        text = clean_text(value)
        if text.startswith("http://") or text.startswith("https://"):
            return text
    return ""


def merge_source_rows(group: pd.DataFrame) -> dict[str, Any]:
    ranked = group.copy()
    ranked["_completeness"] = ranked.apply(lambda row: record_richness_score(row)[0], axis=1)
    ranked["_source_priority"] = ranked["source_database"].map(source_priority).fillna(0)
    ranked = ranked.sort_values(
        ["_completeness", "_source_priority", "open_access_flag"],
        ascending=[False, False, False],
        na_position="last",
    )
    primary = ranked.iloc[0].to_dict()
    merged = {key: value for key, value in primary.items() if not str(key).startswith("_")}
    for column in ["title", "abstract", "authors", "journal", "publication_type", "license"]:
        merged[column] = combine_unique(group[column].tolist(), separator=" || ")
    for column in ["doi", "pmid", "pmcid"]:
        cleaned_values = [clean_text(value) for value in group[column].tolist() if clean_text(value)]
        merged[column] = cleaned_values[0] if cleaned_values else ""
    merged["source_databases"] = combine_unique(group["source_database"].tolist())
    merged["query_names"] = combine_unique(group["query_name"].tolist())
    merged["search_queries"] = combine_unique(group["search_query"].tolist(), separator=" || ")
    merged["source_record_ids"] = combine_unique(group["source_record_id"].tolist())
    merged["open_access_flag"] = bool(group["open_access_flag"].fillna(False).any())
    merged["pdf_url"] = pick_first_url(group["pdf_url"].tolist())
    merged["fulltext_url"] = pick_first_url(group["fulltext_url"].tolist())
    merged["landing_page_url"] = pick_first_url(group["landing_page_url"].tolist())
    merged["candidate_urls_json"] = combine_json_lists(group["candidate_urls_json"].tolist())
    merged["licenses_json"] = combine_json_lists(group["licenses_json"].tolist())
    merged["matched_sources_count"] = int(group["source_database"].nunique())
    merged["matched_rows_count"] = int(len(group))
    return merged


def detect_terms(text: str, terms: list[str]) -> list[str]:
    normalized = normalize_text(text)
    return [term for term in terms if term in normalized]


def likely_review(title: Any, publication_type: Any) -> bool:
    text = normalize_text(title) + " " + normalize_text(publication_type)
    return any(token in text for token in ["review", "systematic review", "meta-analysis"])


def likely_original_research(title: Any, publication_type: Any) -> bool:
    if likely_review(title, publication_type):
        return False
    text = normalize_text(publication_type)
    if not text:
        return True
    if any(token in text for token in ["journal article", "research article", "article"]):
        return True
    return not any(token in text for token in ["editorial", "comment", "news"])


def classify_priority(score: int) -> str:
    if score >= 5:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def safe_filename(text: str, max_len: int = 120) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", clean_text(text))
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    return cleaned[:max_len] or "record"


def first_author(authors_text: Any) -> str:
    text = clean_text(authors_text)
    if not text:
        return "unknown_author"
    first = text.split(";")[0].strip()
    surname = re.split(r"[\s,]+", first)[0]
    return safe_filename(surname.lower(), max_len=40)


def stable_file_stem(row: pd.Series | dict[str, Any]) -> str:
    data = row if isinstance(row, dict) else row.to_dict()
    author = first_author(data.get("authors"))
    year = clean_text(data.get("year")) or "unknown_year"
    title = clean_text(data.get("title")) or clean_text(data.get("doi")) or "untitled"
    title_slug = safe_filename(title.lower(), max_len=60)
    return safe_filename(f"{author}_{year}_{title_slug}", max_len=110)


def content_extension(content_type: str, url: str) -> str:
    lowered_type = clean_text(content_type).lower()
    lowered_url = url.lower()
    if "pdf" in lowered_type or lowered_url.endswith(".pdf"):
        return ".pdf"
    if "xml" in lowered_type or lowered_url.endswith(".xml"):
        return ".xml"
    if "html" in lowered_type or lowered_type.startswith("text/"):
        return ".html"
    return ".bin"


def append_rows_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(pd.DataFrame(rows).columns)
    exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)
