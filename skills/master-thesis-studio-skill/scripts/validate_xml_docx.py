from __future__ import annotations

import argparse
from pathlib import Path
import zipfile

from flat_opc_converter import flat_opc_xml_to_docx, sniff_xml_kind
from word_xml_core import parse_template_xml


def validate(project_dir: str | Path) -> dict[str, object]:
    project = Path(project_dir).resolve()
    xml_path = project / "09_state" / "current_working.xml"
    if not xml_path.exists():
        xml_path = project / "01_template" / "template.flat.xml"
    if not xml_path.exists():
        raise SystemExit("No XML found at 09_state/current_working.xml or 01_template/template.flat.xml")
    kind = sniff_xml_kind(xml_path)
    if kind != "flat_opc":
        raise SystemExit(f"XML is not Flat OPC: {kind}")
    parsed = parse_template_xml(xml_path)
    temp_docx = project / "09_state" / "_validate_rebuild.docx"
    if temp_docx.exists():
        temp_docx.unlink()
    flat_opc_xml_to_docx(xml_path, temp_docx)
    with zipfile.ZipFile(temp_docx, "r") as zf:
        names = set(zf.namelist())
        if "word/document.xml" not in names:
            raise SystemExit("Rebuilt DOCX is missing word/document.xml")
        if "[Content_Types].xml" not in names:
            raise SystemExit("Rebuilt DOCX is missing [Content_Types].xml")
    temp_docx.unlink(missing_ok=True)
    return {
        "xml": str(xml_path),
        "kind": kind,
        "chapters": len(parsed.get("chapters") or []),
        "blocks": len(parsed.get("mapping", {}).get("blocks") or []),
        "docx_rebuild": True,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Flat OPC XML and DOCX rebuildability.")
    ap.add_argument("project_dir")
    args = ap.parse_args(argv)
    result = validate(args.project_dir)
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
