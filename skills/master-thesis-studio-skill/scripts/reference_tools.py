from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def authors_join(authors: list[str]) -> str:
    return ", ".join(authors) if authors else "Unknown Author"


def format_citation(meta: dict[str, Any], style: str) -> str:
    title = meta.get("title") or "Untitled"
    authors = meta.get("authors") or []
    year = str(meta.get("year") or meta.get("publicationDate", "")[:4] or "N/A")
    journal = meta.get("venue") or meta.get("journal") or "Unknown Journal"
    volume = meta.get("volume") or ""
    issue = meta.get("issue") or ""
    pages = meta.get("pages") or ""
    doi = meta.get("doi") or ""
    url = meta.get("url") or ""
    first_author = authors[0] if authors else "Unknown"
    et_al = " et al." if len(authors) > 1 else ""

    if style == "GB/T 7714":
        gb_authors = []
        for name in authors[:3]:
            if "," in name:
                gb_authors.append(name.upper())
            else:
                parts = name.split()
                if len(parts) > 1:
                    last = parts[-1].upper()
                    rest = " ".join(p.upper() for p in parts[:-1])
                    gb_authors.append(f"{last} {rest}".strip())
                else:
                    gb_authors.append(name.upper())
        author_part = ", ".join(gb_authors) if gb_authors else "UNKNOWN AUTHOR"
        if len(authors) > 3:
            author_part += ", et al"
        details = year
        if volume:
            details += f", {volume}"
        if issue:
            details += f"({issue})"
        if pages:
            details += f": {pages}"
        type_mark = "[J]" if volume or issue or meta.get("type") == "journal-article" else "[C]"
        return f"{author_part}. {title}{type_mark}. {journal}, {details}."

    if style == "APA":
        details = ""
        if volume:
            details += f", {volume}"
        if issue:
            details += f"({issue})"
        if pages:
            details += f", {pages}"
        doi_str = f" https://doi.org/{doi}" if doi else (f" {url}" if url else "")
        return f"{authors_join(authors)} ({year}). {title}. {journal}{details}.{doi_str}"

    if style == "IEEE":
        details = ""
        if volume:
            details += f", vol. {volume}"
        if issue:
            details += f", no. {issue}"
        if pages:
            details += f", pp. {pages}"
        return f'{first_author}{et_al}, "{title}," {journal}{details}, {year}.'

    if style == "MLA":
        details = year
        if volume:
            details = f"vol. {volume}, " + details
        if issue:
            details = f"no. {issue}, " + details
        if pages:
            details += f", pp. {pages}"
        return f'{first_author}{et_al}. "{title}." {journal}, {details}.'

    return f"{authors_join(authors)}. {title}. {journal}, {year}."


def format_refs(refs: list[dict[str, Any]], style: str) -> list[dict[str, Any]]:
    updated = []
    for ref in refs:
        new_ref = dict(ref)
        meta = new_ref.get("metadata")
        if isinstance(meta, dict) and meta.get("title"):
            new_ref["description"] = format_citation(meta, style)
        elif not new_ref.get("description"):
            new_ref["description"] = "[需要修复: 缺少参考文献信息]"
        elif "需要修复" not in new_ref["description"]:
            new_ref["description"] = f"{new_ref['description']} [需要修复: 缺少结构化元数据]"
        updated.append(new_ref)
    return updated


def fetch_crossref(title: str) -> dict[str, Any] | None:
    query = urlencode({"query.bibliographic": title, "rows": 1, "mailto": "thesis-skill@example.com"})
    req = Request(f"https://api.crossref.org/works?{query}", headers={"User-Agent": "master-thesis-studio/1.0"})
    with urlopen(req, timeout=60) as res:
        data = json.loads(res.read().decode("utf-8"))
    item = (data.get("message", {}).get("items") or [None])[0]
    if not item:
        return None
    return {
        "title": (item.get("title") or [title])[0],
        "authors": [f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in item.get("author", [])],
        "journal": (item.get("container-title") or [""])[0],
        "year": str(((item.get("published") or {}).get("date-parts") or [[""]])[0][0]),
        "volume": item.get("volume") or "",
        "issue": item.get("issue") or "",
        "pages": item.get("page") or "",
        "doi": item.get("DOI") or "",
        "type": item.get("type") or "",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Format references and optionally enrich metadata.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    fmt = sub.add_parser("format")
    fmt.add_argument("refs_json")
    fmt.add_argument("--style", default="GB/T 7714", choices=["GB/T 7714", "APA", "IEEE", "MLA"])
    fmt.add_argument("--out")

    enrich = sub.add_parser("crossref")
    enrich.add_argument("title")

    args = ap.parse_args(argv)
    if args.cmd == "format":
        path = Path(args.refs_json).resolve()
        refs = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(refs, dict):
            refs = refs.get("references") or []
        updated = format_refs(refs, args.style)
        text = json.dumps(updated, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        else:
            print(text)
    elif args.cmd == "crossref":
        print(json.dumps(fetch_crossref(args.title), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

