from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import shutil
from typing import Any

from word_xml_core import apply_state_to_xml, load_state, render_markdown_references, write_state

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()


def section_id_from_block(block: str) -> str | None:
    m = re.search(r"<!--\s*section_id:\s*([^>]+?)\s*-->", block)
    return m.group(1).strip() if m else None


def extract_after_draft(md: str) -> str:
    m = re.search(r"^##\s+Draft\s*$", md, flags=re.M)
    body = md[m.end() :].strip() if m else md.strip()
    return normalize_placeholder_aliases(remove_markdown_file_header(body))


def normalize_placeholder_aliases(md: str) -> str:
    md = re.sub(r"\[\[\s*TABLE\s*:", "[[TBL:", md, flags=re.I)
    md = re.sub(r"\[\[\s*FIGURE\s*:", "[[FIG:", md, flags=re.I)
    md = re.sub(r"\[\[\s*EQUATION\s*:", "[[EQ:", md, flags=re.I)
    return md


def remove_markdown_file_header(md: str) -> str:
    lines = md.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and re.match(r"^#\s+", lines[0]):
        lines.pop(0)
        while lines and (not lines[0].strip() or re.match(r"^<!--\s*chapter_id:", lines[0].strip())):
            lines.pop(0)
    return "\n".join(lines).strip()


def apply_content_to_chapter(chapter: dict[str, Any], md: str) -> None:
    body = extract_after_draft(md)
    section_blocks = re.split(r"(?=^##\s+)", body, flags=re.M)
    section_map: dict[str, str] = {}
    free_parts: list[str] = []
    for block in section_blocks:
        block = block.strip()
        if not block:
            continue
        if re.match(r"^#\s+", block):
            continue
        sid = section_id_from_block(block)
        content = re.sub(r"^##\s+.*?$", "", block, count=1, flags=re.M)
        content = strip_html_comments(content)
        if sid:
            section_map[sid] = content
        else:
            free_parts.append(strip_html_comments(block))

    def update(node: dict[str, Any]) -> None:
        node_id = node.get("id")
        if node_id in section_map:
            node["content"] = section_map[node_id]
        for child in node.get("subsections") or []:
            update(child)

    for child in chapter.get("subsections") or []:
        update(child)
    if free_parts:
        chapter["content"] = "\n\n".join(p for p in free_parts if p).strip()
    elif chapter.get("subsections"):
        chapter["content"] = ""
    else:
        chapter["content"] = ""


def chapter_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"ch(?:apter)?[_-]?(\d+)", path.stem, flags=re.I)
    number = int(match.group(1)) if match else 10_000
    return number, path.name.lower()


def discover_markdown_drafts(project: Path) -> list[Path]:
    chapter_dir = project / "03_chapters"
    standard = sorted(chapter_dir.glob("ch*_draft.md"), key=chapter_sort_key)
    if standard:
        return standard
    candidates: list[Path] = []
    for path in chapter_dir.glob("ch*.md"):
        stem = path.stem.lower()
        if stem.endswith("_plan") or stem.endswith("-plan") or "plan" in stem:
            continue
        candidates.append(path)
    return sorted(candidates, key=chapter_sort_key)


def title_from_markdown(md: str, fallback: str) -> str:
    for line in md.splitlines():
        match = HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 1:
            return match.group(2).strip().rstrip("#").strip()
    return fallback


def chapter_id_from_markdown(md: str, fallback: str) -> str:
    match = re.search(r"<!--\s*chapter_id:\s*([^>]+?)\s*-->", md)
    return match.group(1).strip() if match else fallback


def clean_markdown_content(lines: list[str]) -> str:
    text = "\n".join(lines).strip()
    return strip_html_comments(normalize_placeholder_aliases(text))


def parse_markdown_chapter(path: Path, index: int) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    chapter_id = chapter_id_from_markdown(raw, f"ch_{index}")
    chapter = {
        "id": chapter_id,
        "title": title_from_markdown(raw, f"Chapter {index}"),
        "level": 1,
        "content": "",
        "subsections": [],
    }
    body = extract_after_draft(raw)
    current: dict[str, Any] = chapter
    current_l2: dict[str, Any] | None = None
    buffer: list[str] = []
    section_count = 0
    subsection_count = 0

    def flush() -> None:
        nonlocal buffer
        current["content"] = clean_markdown_content(buffer)
        buffer = []

    for line in body.splitlines():
        stripped = line.strip()
        match = HEADING_RE.match(stripped)
        if match:
            level = len(match.group(1))
            if level == 1:
                continue
            if level in {2, 3}:
                flush()
                title = match.group(2).strip().rstrip("#").strip()
                if level == 2:
                    section_count += 1
                    subsection_count = 0
                    node = {
                        "id": f"{chapter_id}_sec_{section_count}",
                        "title": title,
                        "level": 2,
                        "content": "",
                        "subsections": [],
                    }
                    chapter["subsections"].append(node)
                    current_l2 = node
                    current = node
                else:
                    subsection_count += 1
                    parent = current_l2 or chapter
                    node = {
                        "id": f"{chapter_id}_sub_{section_count or 1}_{subsection_count}",
                        "title": title,
                        "level": 3,
                        "content": "",
                        "subsections": [],
                    }
                    parent["subsections"].append(node)
                    current = node
                continue

        section_id = section_id_from_block(stripped)
        if section_id and current is not chapter:
            current["id"] = section_id
            continue
        if re.match(r"^<!--\s*chapter_id:", stripped):
            continue
        buffer.append(line)

    flush()
    return chapter


def load_markdown_into_state(project: Path, state: dict[str, Any]) -> dict[str, Any]:
    chapters = state.get("thesis", {}).get("chapters") or []
    l1 = [c for c in chapters if int(c.get("level") or 1) == 1] or chapters
    drafts = discover_markdown_drafts(project)
    uses_standard_contract = bool(drafts) and all(p.stem.lower().endswith("_draft") for p in drafts)
    if drafts and (not uses_standard_contract or len(l1) != len(drafts)):
        chapters = [parse_markdown_chapter(path, i) for i, path in enumerate(drafts, start=1)]
        state.setdefault("thesis", {})["chapters"] = chapters
    else:
        for chapter, draft in zip(l1, drafts):
            apply_content_to_chapter(chapter, draft.read_text(encoding="utf-8"))
    generated_refs = render_markdown_references(chapters)
    refs = list(state.get("references") or [])
    existing_ids = {int(ref.get("id") or 0) for ref in refs}
    for ref in generated_refs:
        if int(ref.get("id") or 0) not in existing_ids:
            refs.append(ref)
            existing_ids.add(int(ref.get("id") or 0))
    state["references"] = refs
    state["step"] = "xml_written"
    return state


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Apply confirmed Markdown drafts to working Flat OPC XML.")
    ap.add_argument("project_dir")
    ap.add_argument("--out", default="09_state/current_working.xml")
    args = ap.parse_args(argv)

    project = Path(args.project_dir).resolve()
    template_xml = project / "01_template" / "template.flat.xml"
    if not template_xml.exists():
        raise SystemExit(f"Missing template XML: {template_xml}")

    state = load_markdown_into_state(project, load_state(project))
    write_state(project, state)

    out = Path(args.out)
    if not out.is_absolute():
        out = project / out
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        snap = project / "09_state" / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        shutil.copy(out, snap)

    apply_state_to_xml(project, template_xml, out, state)
    manifest = {
        "template_xml": str(template_xml),
        "working_xml": str(out),
        "draft_files": [str(p) for p in discover_markdown_drafts(project)],
        "timestamp": datetime.now().isoformat(),
    }
    (project / "09_state" / "current_content_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
