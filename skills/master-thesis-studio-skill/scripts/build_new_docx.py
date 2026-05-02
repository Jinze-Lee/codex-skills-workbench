from __future__ import annotations

import argparse
from pathlib import Path

from flat_opc_converter import flat_opc_xml_to_docx


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build a new DOCX from the current Flat OPC XML state.")
    ap.add_argument("project_dir")
    ap.add_argument("--name", default="thesis_draft_v1.docx")
    ap.add_argument("--xml", default="09_state/current_working.xml")
    args = ap.parse_args(argv)

    project = Path(args.project_dir).resolve()
    xml_path = Path(args.xml)
    if not xml_path.is_absolute():
        xml_path = project / xml_path
    if not xml_path.exists():
        raise SystemExit(f"Missing working XML: {xml_path}")
    out_dir = project / "10_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_docx = out_dir / args.name
    if out_docx.name == "original_template.docx":
        raise SystemExit("Refusing to overwrite original_template.docx")
    flat_opc_xml_to_docx(xml_path, out_docx)
    print(out_docx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

