from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
import posixpath
from pathlib import Path
import re
import shutil
import zipfile
from typing import Any

from lxml import etree

from generate_planning_files import generate as generate_planning_files
from init_thesis_workspace import init_workspace
from word_xml_core import (
    NS,
    W_NS,
    build_heading_styles,
    caption_desc_for_kind,
    caption_kind,
    extract_style_id,
    has_image_like,
    normalize_title,
    para_text,
    table_to_markdown,
)

R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def local_name(node: etree._Element) -> str:
    return etree.QName(node).localname


def safe_rel_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("/")


def doc_rel_target_to_zip_name(target: str) -> str:
    target = target.replace("\\", "/")
    normalized = posixpath.normpath(posixpath.join("word", target))
    return normalized.lstrip("/")


def read_xml(zf: zipfile.ZipFile, name: str) -> etree._Element | None:
    if name not in zf.namelist():
        return None
    parser = etree.XMLParser(remove_blank_text=False, recover=True)
    return etree.fromstring(zf.read(name), parser)


def read_relationships(zf: zipfile.ZipFile) -> dict[str, str]:
    root = read_xml(zf, "word/_rels/document.xml.rels")
    if root is None:
        return {}
    rels: dict[str, str] = {}
    for rel in root.findall(f".//{{{REL_NS}}}Relationship"):
        rel_id = rel.get("Id")
        target = rel.get("Target")
        if rel_id and target:
            rels[rel_id] = safe_rel_path(target)
    return rels


def image_rel_ids(paragraph: etree._Element) -> list[str]:
    rel_ids: list[str] = []
    for node in paragraph.findall(".//*[@r:embed]", namespaces=NS) + paragraph.findall(".//*[@r:id]", namespaces=NS):
        rel_id = node.get(f"{{{R_NS}}}embed") or node.get(f"{{{R_NS}}}id")
        if rel_id and rel_id not in rel_ids:
            rel_ids.append(rel_id)
    return rel_ids


def adjacent_caption(nodes: list[etree._Element], index: int, kind: str) -> str:
    offsets = (1, -1) if kind == "figure" else (-1, 1)
    for offset in offsets:
        pos = index + offset
        if 0 <= pos < len(nodes):
            node = nodes[pos]
            if local_name(node) == "p" and caption_kind(node) == kind:
                return caption_desc_for_kind(node, kind)
    return ""


def table_rows(tbl: etree._Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in tbl.findall("./w:tr", namespaces=NS):
        row: list[str] = []
        for tc in tr.findall("./w:tc", namespaces=NS):
            value = " ".join(
                normalize_title(para_text(p))
                for p in tc.findall("./w:p", namespaces=NS)
                if normalize_title(para_text(p))
            )
            row.append(value)
        if any(cell for cell in row):
            rows.append(row)
    return rows


def is_usable_table(rows: list[list[str]]) -> bool:
    if len(rows) < 2:
        return False
    flat = [cell.strip() for row in rows for cell in row]
    if not any(flat):
        return False
    if rows[0][:2] == ["项目", "内容"] and any("待补充" in cell for cell in flat):
        return False
    return True


def extension_from_target(target: str) -> str:
    suffix = Path(target).suffix.lower()
    return suffix if suffix else ".bin"


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(rows)


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    col_count = max(len(row) for row in rows)
    padded = [row + [""] * (col_count - len(row)) for row in rows]

    def fmt(row: list[str]) -> str:
        return "| " + " | ".join(cell.replace("|", r"\|") for cell in row) + " |"

    lines = [fmt(padded[0]), "| " + " | ".join(["---"] * col_count) + " |"]
    lines.extend(fmt(row) for row in padded[1:])
    return "\n".join(lines)


def extract_assets_from_docx(docx: Path, project: Path) -> dict[str, Any]:
    figures: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    with zipfile.ZipFile(docx, "r") as zf:
        document = read_xml(zf, "word/document.xml")
        if document is None:
            raise SystemExit(f"Missing word/document.xml in {docx}")
        styles = read_xml(zf, "word/styles.xml")
        rels = read_relationships(zf)
        heading_styles = build_heading_styles(styles)
        body = document.find(".//w:body", namespaces=NS)
        if body is None:
            raise SystemExit(f"Missing w:body in {docx}")

        current_chapter: dict[str, Any] | None = None
        chapter_index = 0
        chapter_fig_count = 0
        chapter_tbl_count = 0
        nodes = [node for node in body if local_name(node) in {"p", "tbl"}]

        for idx, node in enumerate(nodes):
            kind = local_name(node)
            if kind == "p":
                text = normalize_title(para_text(node))
                style_id = extract_style_id(node)
                if style_id == heading_styles.get(1) and text:
                    chapter_index += 1
                    current_chapter = {
                        "index": chapter_index,
                        "title": text,
                        "id": f"ch{chapter_index:02d}",
                    }
                    chapter_fig_count = 0
                    chapter_tbl_count = 0
                    continue

            if current_chapter is None:
                continue

            if kind == "p" and has_image_like(node):
                    rel_ids = image_rel_ids(node)
                    desc = adjacent_caption(nodes, idx, "figure") or f"图{current_chapter['index']}-{chapter_fig_count + 1}"
                    for rel_id in rel_ids:
                        target = rels.get(rel_id, "")
                        media_name = safe_rel_path(target)
                        zip_name = doc_rel_target_to_zip_name(target) if target else ""
                    usable = bool(media_name and zip_name in zf.namelist())
                    chapter_fig_count += 1
                    out_name = f"fig_ch{current_chapter['index']:02d}_{chapter_fig_count:02d}{extension_from_target(media_name)}"
                    out_path = project / "04_figures" / out_name
                    if usable:
                        out_path.write_bytes(zf.read(zip_name))
                    figures.append(
                        {
                            "id": f"fig_ch{current_chapter['index']:02d}_{chapter_fig_count:02d}",
                            "chapter_index": current_chapter["index"],
                            "chapter_title": current_chapter["title"],
                            "caption": desc,
                            "rel_id": rel_id,
                            "source": zip_name,
                            "file": str(out_path.relative_to(project)) if usable else "",
                            "usable": usable,
                            "note": "real embedded image" if usable else "image relationship target not found",
                        }
                    )

            elif kind == "tbl":
                rows = table_rows(node)
                chapter_tbl_count += 1
                desc = adjacent_caption(nodes, idx, "table") or f"表{current_chapter['index']}-{chapter_tbl_count}"
                tbl_id = f"tbl_ch{current_chapter['index']:02d}_{chapter_tbl_count:02d}"
                md_path = project / "05_tables" / f"{tbl_id}.md"
                csv_path = project / "05_tables" / f"{tbl_id}.csv"
                usable = is_usable_table(rows)
                md_path.write_text(markdown_table(rows) + "\n", encoding="utf-8")
                write_csv(csv_path, rows)
                tables.append(
                    {
                        "id": tbl_id,
                        "chapter_index": current_chapter["index"],
                        "chapter_title": current_chapter["title"],
                        "caption": desc,
                        "rows": len(rows),
                        "columns": max((len(row) for row in rows), default=0),
                        "markdown": str(md_path.relative_to(project)),
                        "csv": str(csv_path.relative_to(project)),
                        "usable": usable,
                        "note": "real Word table" if usable else "empty or placeholder-like table",
                    }
                )

    return {"figures": figures, "tables": tables}


def infer_title_from_docx(docx: Path) -> str:
    with zipfile.ZipFile(docx, "r") as zf:
        document = read_xml(zf, "word/document.xml")
        if document is None:
            return ""
        body_text = "\n".join(normalize_title(para_text(p)) for p in document.findall(".//w:p", namespaces=NS))
    match = re.search(r"《([^》]{4,80})》", body_text)
    if match:
        return match.group(1).strip()
    for line in body_text.splitlines():
        value = normalize_title(line)
        if 6 <= len(value) <= 80 and not re.search(r"^(摘\s*要|Abstract|目\s*录|表格目录|插图目录)$", value, re.I):
            return value
    return ""


def update_project_title(project: Path, title: str) -> None:
    if not title:
        return
    state_path = project / "09_state" / "project_state.json"
    if not state_path.exists():
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.setdefault("thesis", {})["title"] = title
    state["timestamp"] = datetime.now().isoformat()
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def write_asset_manifests(project: Path, assets: dict[str, Any]) -> None:
    figure_lines = ["# Figures Manifest", "", "Extracted real embedded figures from the source Word file.", ""]
    for fig in assets["figures"]:
        flag = "usable" if fig["usable"] else "not usable"
        figure_lines.append(
            f"- `{fig['id']}` | 第{fig['chapter_index']}章 | {fig['caption']} | {fig['file'] or fig['source']} | {flag}"
        )
    if not assets["figures"]:
        figure_lines.append("- No real embedded figures found.")
    (project / "04_figures" / "figures_manifest.md").write_text("\n".join(figure_lines) + "\n", encoding="utf-8")

    table_lines = ["# Tables Manifest", "", "Extracted real Word tables from chapter content.", ""]
    for tbl in assets["tables"]:
        flag = "usable" if tbl["usable"] else "not usable"
        table_lines.append(
            f"- `{tbl['id']}` | 第{tbl['chapter_index']}章 | {tbl['caption']} | {tbl['rows']}x{tbl['columns']} | {tbl['markdown']} | {flag}"
        )
    if not assets["tables"]:
        table_lines.append("- No real Word tables found.")
    (project / "05_tables" / "tables_manifest.md").write_text("\n".join(table_lines) + "\n", encoding="utf-8")

    state_path = project / "09_state" / "reverse_parse_assets.json"
    state_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2), encoding="utf-8")


def write_report(project: Path, docx: Path, assets: dict[str, Any]) -> None:
    usable_figures = sum(1 for item in assets["figures"] if item.get("usable"))
    usable_tables = sum(1 for item in assets["tables"] if item.get("usable"))
    report = f"""# Reverse Parse Report

Source Word: `{docx}`

Generated at: {datetime.now().isoformat()}

## Summary

- Figures found: {len(assets["figures"])}
- Usable figures: {usable_figures}
- Tables found: {len(assets["tables"])}
- Usable tables: {usable_tables}

## Outputs

- Chapter drafts: `03_chapters/`
- Extracted figures: `04_figures/`
- Extracted tables: `05_tables/`
- Asset state: `09_state/reverse_parse_assets.json`
- Parsed XML structure: `09_state/parsed_structure.json`

## Notes

- A figure is usable only when the Word paragraph contains a real embedded image relationship and the media file exists in `word/media`.
- A table is usable only when it contains non-empty cell data and is not the fallback `项目/内容/待补充` placeholder pattern.
- Assets are mapped while walking Word body content under the current level-1 chapter heading, so front matter and loose placeholders are not treated as chapter resources.
"""
    (project / "00_project" / "reverse_parse_report.md").write_text(report, encoding="utf-8")


def reverse_parse(project_dir: str | Path, docx_path: str | Path, force: bool = False) -> Path:
    project = Path(project_dir).resolve()
    docx = Path(docx_path).resolve()
    if project.exists() and any(project.iterdir()) and force:
        shutil.rmtree(project)
    init_workspace(project, docx, force=force)
    title = infer_title_from_docx(docx)
    update_project_title(project, title)
    generate_planning_files(project)
    assets = extract_assets_from_docx(docx, project)
    write_asset_manifests(project, assets)
    write_report(project, docx, assets)
    print(project)
    return project


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Reverse parse a user's DOCX into a thesis workspace with chapter, figure, and table assets.")
    ap.add_argument("project_dir")
    ap.add_argument("--docx", required=True, help="Source Word .docx to reverse parse.")
    ap.add_argument("--force", action="store_true", help="Delete and rebuild the target project directory if it exists.")
    args = ap.parse_args(argv)
    reverse_parse(args.project_dir, args.docx, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
