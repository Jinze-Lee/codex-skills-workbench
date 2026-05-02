from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from word_xml_core import default_outline, load_state, write_state


def flatten(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ch in chapters:
        out.append(ch)
        out.extend(flatten(ch.get("subsections") or []))
    return out


def outline_lines(chapters: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for ch in chapters:
        indent = "  " * (int(ch.get("level") or 1) - 1)
        lines.append(f"{indent}- {ch.get('title', '未命名章节')}")
        lines.extend(outline_lines(ch.get("subsections") or []))
    return lines


def chapter_file_index(chapter: dict[str, Any], fallback: int) -> str:
    return f"{fallback:02d}"


def make_plan(chapter: dict[str, Any]) -> str:
    subs = chapter.get("subsections") or []
    section_lines = "\n".join(f"- {s.get('title', '未命名小节')}" for s in subs) or "- 待确认"
    return f"""# {chapter.get('title', '未命名章节')}
<!-- chapter_id: {chapter.get('id', '')} -->

## Chapter Purpose

待确认：本章在整篇论文中的作用、核心论点、输入输出关系。

## Sections

{section_lines}

## Figures And Tables

- Figures: 待确认
- Tables: 待确认

## Formulas

- 待确认

## Code And Data

- Code: 待确认
- Data: 待确认

## References

- 待确认
"""


def make_draft(chapter: dict[str, Any]) -> str:
    content = (chapter.get("content") or "").strip()
    sections = []
    for child in chapter.get("subsections") or []:
        child_content = (child.get("content") or "").strip()
        sections.append(
            f"## {child.get('title', '未命名小节')}\n<!-- section_id: {child.get('id', '')} -->\n\n{child_content}\n"
        )
    body = "\n".join(sections).strip() or content or "在此撰写本章已确认内容。"
    return f"""# {chapter.get('title', '未命名章节')}
<!-- chapter_id: {chapter.get('id', '')} -->

## Draft

{body}
"""


def generate(project_dir: str | Path) -> None:
    project = Path(project_dir).resolve()
    state = load_state(project)
    parsed_path = project / "09_state" / "parsed_structure.json"
    if parsed_path.exists() and not state.get("thesis", {}).get("chapters"):
        parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
        state["thesis"] = {
            "title": state.get("thesis", {}).get("title") or "未命名硕士论文",
            "chapters": parsed.get("chapters") or default_outline(),
        }
    chapters = state.get("thesis", {}).get("chapters") or default_outline()
    project.joinpath("03_chapters").mkdir(parents=True, exist_ok=True)

    l1 = [c for c in chapters if int(c.get("level") or 1) == 1] or chapters
    for i, ch in enumerate(l1, start=1):
        idx = chapter_file_index(ch, i)
        plan_path = project / "03_chapters" / f"ch{idx}_plan.md"
        draft_path = project / "03_chapters" / f"ch{idx}_draft.md"
        if not plan_path.exists():
            plan_path.write_text(make_plan(ch), encoding="utf-8")
        if not draft_path.exists():
            draft_path.write_text(make_draft(ch), encoding="utf-8")

    index = project / "00_project" / "thesis_master_index.md"
    thesis_title = state.get("thesis", {}).get("title") or "未命名硕士论文"
    index.write_text(
        "# Thesis Master Index\n\n"
        f"Thesis title: {thesis_title}\n\n"
        f"Updated: {datetime.now().isoformat()}\n\n"
        "## Outline\n\n"
        + "\n".join(outline_lines(chapters))
        + "\n",
        encoding="utf-8",
    )
    progress = project / "00_project" / "writing_progress.md"
    progress.write_text(
        "# Writing Progress\n\n"
        + "\n".join(f"- [ ] {c.get('title', '未命名章节')}" for c in l1)
        + "\n",
        encoding="utf-8",
    )
    write_state(project, state)
    print(project / "03_chapters")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate Markdown planning and draft files.")
    ap.add_argument("project_dir")
    args = ap.parse_args(argv)
    generate(args.project_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
