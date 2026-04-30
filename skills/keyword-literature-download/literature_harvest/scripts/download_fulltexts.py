from __future__ import annotations

import argparse
import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

from harvest_utils import (
    LOG_DIR,
    MERGED_DIR,
    PDF_DIR,
    append_rows_csv,
    clean_text,
    content_extension,
    ensure_directories,
    load_config,
    stable_file_stem,
    write_csv,
    write_markdown,
)


PAYWALL_MARKERS = [
    "subscription required",
    "purchase this article",
    "access through your institution",
    "institutional access",
    "paywall",
    "buy article",
]


def parse_candidate_urls(row: pd.Series) -> list[str]:
    candidates = []
    for key in ["pdf_url", "fulltext_url", "landing_page_url"]:
        url = clean_text(row.get(key))
        if url:
            candidates.append(url)
    raw_json = row.get("candidate_urls_json")
    if isinstance(raw_json, str) and raw_json.strip():
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, str):
                        url = clean_text(item)
                    elif isinstance(item, dict):
                        url = clean_text(item.get("url"))
                    else:
                        url = ""
                    if url:
                        candidates.append(url)
        except json.JSONDecodeError:
            pass
    unique = []
    seen = set()
    for url in candidates:
        if not (url.startswith("http://") or url.startswith("https://")):
            continue
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def attempt_download(url: str, timeout: int) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "keyword-research-harvest/0.1",
            "Accept": "application/pdf, application/xml, text/xml, text/html;q=0.9, */*;q=0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
        payload = response.read()
        content_type = clean_text(response.headers.get("Content-Type")).lower()
        final_url = clean_text(response.geturl())
        status_code = int(getattr(response, "status", 200))
    return {
        "status_code": status_code,
        "content_type": content_type,
        "final_url": final_url,
        "payload": payload,
    }


def classify_payload(payload: bytes, content_type: str) -> str:
    sample = payload[:2000].decode("utf-8", errors="ignore").lower()
    if "pdf" in content_type or payload.startswith(b"%PDF"):
        return "pdf"
    if "xml" in content_type or sample.lstrip().startswith("<?xml"):
        return "xml"
    if "html" in content_type or "<html" in sample:
        return "html"
    return "other"


def resolve_output_path(raw_path: str | None, default_path: Path, base_dir: Path) -> Path:
    if not raw_path:
        return default_path.resolve()
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def is_pdf_payload(payload: bytes) -> bool:
    return payload[:1024].lstrip().startswith(b"%PDF")


def has_pdf_signature(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(1024).lstrip().startswith(b"%PDF")
    except OSError:
        return False


def ensure_pdf_only_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    non_pdf_files = [
        item
        for item in path.iterdir()
        if item.is_file() and (item.suffix.lower() != ".pdf" or not has_pdf_signature(item))
    ]
    if non_pdf_files:
        preview = ", ".join(str(item) for item in non_pdf_files[:5])
        suffix = " ..." if len(non_pdf_files) > 5 else ""
        raise RuntimeError(
            f"PDF output directory must contain only valid PDF files. Found: {preview}{suffix}"
        )


def save_auxiliary_payload(
    row: pd.Series,
    payload: bytes,
    kind: str,
    content_type: str,
    final_url: str,
    non_pdf_dir: Path,
) -> str:
    if kind not in {"html", "xml"}:
        return ""
    extension = ".html" if kind == "html" else ".xml"
    if extension == ".pdf":
        extension = content_extension(content_type, final_url)
    non_pdf_dir.mkdir(parents=True, exist_ok=True)
    output = non_pdf_dir / f"{stable_file_stem(row)}{extension}"
    output.write_bytes(payload)
    return str(output)


def looks_paywalled(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in PAYWALL_MARKERS)


def build_download_report(status_df: pd.DataFrame) -> str:
    success_count = int((status_df["status"] == "success").sum())
    lines = [
        "# Fulltext Download Report",
        "",
        f"- Total attempted records: `{len(status_df)}`",
        f"- Successful downloads: `{success_count}`",
        f"- Metadata-only outcomes: `{int((status_df['status'] == 'metadata_only').sum())}`",
        f"- Inaccessible outcomes: `{int((status_df['status'] == 'inaccessible').sum())}`",
        f"- Broken link outcomes: `{int((status_df['status'] == 'broken_link').sum())}`",
        f"- Rate-limited outcomes: `{int((status_df['status'] == 'rate_limited').sum())}`",
        "",
        "## Notes",
        "",
        "- Only direct, legal URLs from scholarly APIs were used.",
        "- No paywall bypassing was attempted.",
        "- XML/HTML helper files are cached outside the PDF output folder.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--pdf-output-dir", default=None, help="Folder for generated PDFs only")
    args = parser.parse_args()

    ensure_directories()
    config = load_config(args.config)
    config_path = Path(args.config).resolve() if args.config else (Path(__file__).resolve().parent / "config_search_terms.yaml")
    download_config = config.get("download", {})
    pdf_dir = resolve_output_path(
        args.pdf_output_dir or download_config.get("pdf_output_dir") or config.get("pdf_output_dir"),
        PDF_DIR,
        config_path.parent,
    )
    non_pdf_dir = LOG_DIR.parent / "download_work" / "non_pdf_payloads"
    ensure_pdf_only_directory(pdf_dir)
    non_pdf_dir.mkdir(parents=True, exist_ok=True)
    if not config.get("download", {}).get("enabled", True):
        write_csv(pd.DataFrame(), LOG_DIR / "download_status.csv")
        write_markdown(
            "# Fulltext Download Report\n\nDownloading is disabled in config.\n",
            LOG_DIR.parent / "reports" / "fulltext_download_report.md",
        )
        return

    priority_path = MERGED_DIR / "keyword_research_candidate_priority_table.csv"
    priority_df = pd.read_csv(priority_path)
    allowed_priorities = set(config.get("download", {}).get("priority_levels", ["high", "medium"]))
    max_attempts = int(config.get("download", {}).get("max_attempts_per_record", 5))
    timeout_seconds = int(config.get("download", {}).get("timeout_seconds", 45))
    delay_seconds = float(config.get("delay_seconds", {}).get("download", 0.25))
    log_path = LOG_DIR / "download_status.csv"

    existing_df = pd.read_csv(log_path) if log_path.exists() else pd.DataFrame()
    processed_keys = set(existing_df.get("dedup_group_key", pd.Series(dtype=str)).fillna("").tolist())
    existing_files = {
        path.stem.lower(): str(path)
        for path in pdf_dir.glob("*.pdf")
        if path.is_file() and has_pdf_signature(path)
    }

    target_df = priority_df.loc[
        priority_df["likely_priority"].isin(allowed_priorities)
    ].copy()
    target_df = target_df.loc[
        ~target_df["dedup_group_key"].fillna("").isin(processed_keys)
    ].copy()
    if args.max_records is not None and args.max_records > 0:
        target_df = target_df.head(args.max_records).copy()
    status_rows = []

    for _, row in target_df.iterrows():
        dedup_key = clean_text(row.get("dedup_group_key"))
        stem = stable_file_stem(row).lower()
        if stem in existing_files:
            row_status = {
                "dedup_group_key": dedup_key,
                "priority_rank": row.get("priority_rank"),
                "likely_priority": clean_text(row.get("likely_priority")),
                "title": clean_text(row.get("title")),
                "doi": clean_text(row.get("doi")),
                "pmid": clean_text(row.get("pmid")),
                "pmcid": clean_text(row.get("pmcid")),
                "status": "success",
                "reason": "existing_file",
                "attempt_count": 0,
                "attempted_url_count": 0,
                "selected_url": "",
                "content_format": "pdf",
                "local_file_path_if_downloaded": existing_files[stem],
                "auxiliary_file_path": "",
            }
            status_rows.append(row_status)
            append_rows_csv(log_path, [row_status])
            continue

        candidate_urls = parse_candidate_urls(row)[:max_attempts]
        record_status = "metadata_only"
        reason = "no_candidate_url"
        downloaded_path = ""
        auxiliary_path = ""
        chosen_url = ""
        content_format = ""
        attempt_count = 0

        for url in candidate_urls:
            attempt_count += 1
            try:
                response = attempt_download(url, timeout_seconds)
                payload = response["payload"]
                content_type = response["content_type"]
                final_url = response["final_url"] or url
                kind = classify_payload(payload, content_type)
                if kind == "pdf":
                    if not is_pdf_payload(payload):
                        record_status = "metadata_only"
                        reason = "pdf_signature_missing"
                        chosen_url = final_url
                        content_format = "not_pdf"
                        continue
                    filename = stable_file_stem(row) + ".pdf"
                    output_path = pdf_dir / filename
                    output_path.write_bytes(payload)
                    record_status = "success"
                    reason = "downloaded"
                    downloaded_path = str(output_path)
                    chosen_url = final_url
                    content_format = "pdf"
                    break
                elif kind == "xml":
                    auxiliary_path = save_auxiliary_payload(row, payload, kind, content_type, final_url, non_pdf_dir)
                    record_status = "non_pdf_saved"
                    reason = "xml_saved_for_second_pass"
                    chosen_url = final_url
                    content_format = "xml"
                    continue
                elif kind == "html":
                    html_text = payload[:25000].decode("utf-8", errors="ignore")
                    if looks_paywalled(html_text):
                        record_status = "inaccessible"
                        reason = "paywall_detected"
                        chosen_url = final_url
                        content_format = "html"
                        continue
                    auxiliary_path = save_auxiliary_payload(row, payload, kind, content_type, final_url, non_pdf_dir)
                    record_status = "non_pdf_saved"
                    reason = "html_saved_for_second_pass"
                    chosen_url = final_url
                    content_format = "html"
                    continue
                else:
                    record_status = "metadata_only"
                    reason = f"non_pdf_payload_{kind}"
                    chosen_url = final_url
                    content_format = kind
                    continue
            except urllib.error.HTTPError as exc:
                code = int(getattr(exc, "code", 0))
                if code == 429:
                    record_status = "rate_limited"
                    reason = f"http_{code}"
                    chosen_url = url
                    break
                if code in {401, 402, 403}:
                    record_status = "inaccessible"
                    reason = f"http_{code}"
                    chosen_url = url
                    continue
                if code in {404, 410}:
                    record_status = "broken_link"
                    reason = f"http_{code}"
                    chosen_url = url
                    continue
                record_status = "metadata_only"
                reason = f"http_{code}"
                chosen_url = url
                continue
            except Exception as exc:
                record_status = "metadata_only"
                reason = type(exc).__name__
                chosen_url = url
                continue
            finally:
                time.sleep(delay_seconds)

        row_status = {
            "dedup_group_key": dedup_key,
            "priority_rank": row.get("priority_rank"),
            "likely_priority": clean_text(row.get("likely_priority")),
            "title": clean_text(row.get("title")),
            "doi": clean_text(row.get("doi")),
            "pmid": clean_text(row.get("pmid")),
            "pmcid": clean_text(row.get("pmcid")),
            "status": record_status,
            "reason": reason,
            "attempt_count": attempt_count,
            "attempted_url_count": len(candidate_urls),
            "selected_url": chosen_url,
            "content_format": content_format,
            "local_file_path_if_downloaded": downloaded_path,
            "auxiliary_file_path": auxiliary_path,
        }
        status_rows.append(row_status)
        append_rows_csv(log_path, [row_status])

    status_df = pd.read_csv(log_path) if log_path.exists() else pd.DataFrame(status_rows)
    if not status_df.empty:
        # Keep the latest result per dedup key when resumed across runs.
        status_df = status_df.drop_duplicates(subset=["dedup_group_key"], keep="last")
    write_csv(status_df, LOG_DIR / "download_status.csv")
    write_markdown(
        build_download_report(status_df),
        LOG_DIR.parent / "reports" / "fulltext_download_report.md",
    )
    ensure_pdf_only_directory(pdf_dir)


if __name__ == "__main__":
    main()
