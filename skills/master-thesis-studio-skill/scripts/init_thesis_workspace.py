from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys

from flat_opc_converter import docx_to_flat_opc_xml
from word_xml_core import default_outline, parse_template_xml, write_state


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL_ROOT / "templates"
DEFAULT_WORD_TEMPLATE = SKILL_ROOT / "examples" / "Template.docx"
SUPPORTED_TEMPLATE_SUFFIXES = {".docx", ".dotx"}

DIRS = [
    "00_project",
    "01_template",
    "03_chapters",
    "04_figures",
    "05_tables",
    "06_code",
    "07_data",
    "08_refs",
    "09_state",
    "10_output",
]


def copy_if_missing(src_name: str, dst: Path) -> None:
    src = TEMPLATES / src_name
    if src.exists() and not dst.exists():
        shutil.copy(src, dst)


def resolve_template_path(template: str | Path | None) -> tuple[Path, bool]:
    if template is None:
        src = DEFAULT_WORD_TEMPLATE
        is_default = True
    else:
        src = Path(template).expanduser().resolve()
        is_default = False

    if not src.exists():
        raise SystemExit(f"Template not found: {src}")
    if not src.is_file():
        raise SystemExit(f"Template is not a file: {src}")
    if src.suffix.lower() not in SUPPORTED_TEMPLATE_SUFFIXES:
        allowed = ", ".join(sorted(SUPPORTED_TEMPLATE_SUFFIXES))
        raise SystemExit(f"Template must be a Word template file ({allowed}): {src}")
    return src, is_default


def init_workspace(project_dir: str | Path, template: str | Path | None = None, force: bool = False) -> Path:
    project = Path(project_dir).resolve()
    if project.exists() and any(project.iterdir()) and not force:
        raise SystemExit(f"Project directory is not empty: {project}")
    project.mkdir(parents=True, exist_ok=True)
    for rel in DIRS:
        (project / rel).mkdir(parents=True, exist_ok=True)

    copy_if_missing("project_manifest.md", project / "00_project" / "project_manifest.md")
    copy_if_missing("thesis_master_index.md", project / "00_project" / "thesis_master_index.md")
    copy_if_missing("figures_manifest.md", project / "04_figures" / "figures_manifest.md")
    copy_if_missing("tables_manifest.md", project / "05_tables" / "tables_manifest.md")
    copy_if_missing("code_manifest.md", project / "06_code" / "code_manifest.md")
    copy_if_missing("data_manifest.md", project / "07_data" / "data_manifest.md")

    progress = project / "00_project" / "writing_progress.md"
    if not progress.exists():
        progress.write_text("# Writing Progress\n\n- Initialized workspace.\n", encoding="utf-8")
    decisions = project / "00_project" / "decisions_log.md"
    if not decisions.exists():
        decisions.write_text("# Decisions Log\n\n", encoding="utf-8")

    src, is_default_template = resolve_template_path(template)
    original = project / "01_template" / "original_template.docx"
    if not original.exists() or force:
        shutil.copy(src, original)
    template_xml = project / "01_template" / "template.flat.xml"
    docx_to_flat_opc_xml(original, template_xml)
    parsed = parse_template_xml(template_xml)
    (project / "09_state" / "parsed_structure.json").write_text(
        json_dumps(parsed), encoding="utf-8"
    )
    template_meta = {
        "source_path": str(src),
        "source_name": src.name,
        "bundled_default": is_default_template,
        "stored_as": "01_template/original_template.docx",
        "supported_input_extensions": sorted(SUPPORTED_TEMPLATE_SUFFIXES),
    }
    (project / "09_state" / "template_source.json").write_text(
        json_dumps(template_meta), encoding="utf-8"
    )

    state = {
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "step": "initialized",
        "thesis": {
            "title": "未命名硕士论文",
            "chapters": parsed.get("chapters") or default_outline(),
        },
        "references": [],
        "styleSettings": {
            "template": template_meta,
        },
    }
    write_state(project, state)
    print(project)
    return project


def json_dumps(data: object) -> str:
    import json

    return json.dumps(data, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Initialize a portable master's thesis workspace.")
    ap.add_argument("project_dir")
    ap.add_argument(
        "--template",
        help="Optional user-selected Word .docx/.dotx template. Defaults to examples/Template.docx.",
    )
    ap.add_argument("--force", action="store_true", help="Allow writing into an existing workspace.")
    args = ap.parse_args(argv)
    init_workspace(args.project_dir, args.template, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
