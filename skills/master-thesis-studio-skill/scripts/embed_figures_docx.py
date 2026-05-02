from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import zipfile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

NS = {"w": W_NS, "r": R_NS, "rel": REL_NS, "wp": WP_NS, "a": A_NS, "pic": PIC_NS, "ct": CT_NS}


def qn(ns: str, local: str) -> str:
    return f"{{{ns}}}{local}"


def para_text(p: etree._Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", namespaces=NS)).strip()


def normalize_key(text: str) -> str:
    return "".join(ch.lower() for ch in (text or "") if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def caption_desc_from_text(text: str) -> str:
    value = re.sub(r"\s+", " ", text or "").strip()
    value = re.sub(r"^图\s*", "", value)
    value = re.sub(r"^[\(（]?\s*[零〇一二三四五六七八九十百\d]+(?:[-.．]\d+)*(?:\s*[)）])?\s*", "", value)
    value = re.sub(r"^[\s:：、.．-]+", "", value)
    return value.strip() or re.sub(r"\s+", " ", text or "").strip()


def is_figure_caption(p: etree._Element) -> bool:
    text = re.sub(r"\s+", " ", para_text(p)).strip()
    return bool(re.match(r"^图\s*[（(]?[零〇一二三四五六七八九十百\d]", text))


def next_rid(rels_root: etree._Element) -> str:
    max_id = 0
    for rel in rels_root.findall("rel:Relationship", namespaces=NS):
        rid = rel.get("Id") or ""
        if rid.startswith("rId"):
            try:
                max_id = max(max_id, int(rid[3:]))
            except ValueError:
                pass
    return f"rId{max_id + 1}"


def ensure_svg_content_type(types_root: etree._Element) -> None:
    for node in types_root.findall("ct:Default", namespaces=NS):
        if node.get("Extension") == "svg":
            return
    default = etree.SubElement(types_root, qn(CT_NS, "Default"))
    default.set("Extension", "svg")
    default.set("ContentType", "image/svg+xml")


def drawing_para(rel_id: str, name: str, cx: int = 4800000, cy: int = 2700000) -> etree._Element:
    return etree.fromstring(f'''<w:p xmlns:w="{W_NS}" xmlns:r="{R_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}" xmlns:pic="{PIC_NS}">
  <w:pPr><w:jc w:val="center"/></w:pPr>
  <w:r>
    <w:drawing>
      <wp:inline distT="0" distB="0" distL="0" distR="0">
        <wp:extent cx="{cx}" cy="{cy}"/>
        <wp:effectExtent l="0" t="0" r="0" b="0"/>
        <wp:docPr id="1" name="{name}"/>
        <wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
        <a:graphic>
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic>
              <pic:nvPicPr><pic:cNvPr id="0" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>
              <pic:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
              <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>'''.encode("utf-8"))


def is_image_placeholder_text(text: str) -> bool:
    compact = re.sub(r"\s+", "", text or "")
    return bool(re.fullmatch(r"[（(]?在此处插入图(?:片)?(?:[:：].*?)?[）)]?", compact))


def placeholder_slots(doc_root: etree._Element) -> list[dict[str, object]]:
    paragraphs = doc_root.findall(".//w:p", namespaces=NS)
    slots: list[dict[str, object]] = []
    for idx, para in enumerate(paragraphs):
        if not is_image_placeholder_text(para_text(para)):
            continue
        caption_para = None
        if idx + 1 < len(paragraphs) and is_figure_caption(paragraphs[idx + 1]):
            caption_para = paragraphs[idx + 1]
        elif idx > 0 and is_figure_caption(paragraphs[idx - 1]):
            caption_para = paragraphs[idx - 1]
        caption_text = para_text(caption_para) if caption_para is not None else ""
        desc = caption_desc_from_text(caption_text) if caption_text else ""
        slots.append({"para": para, "desc": desc, "caption_text": caption_text, "index": idx})
    return slots


def assign_figures_to_slots(slots: list[dict[str, object]], figures: list[Path]) -> list[tuple[dict[str, object], Path]]:
    assignments: list[tuple[dict[str, object], Path]] = []
    used: set[Path] = set()
    normalized_files = [(fig, normalize_key(fig.stem)) for fig in figures]

    for slot in slots:
        desc_key = normalize_key(str(slot.get("desc") or ""))
        if not desc_key:
            continue
        matched: Path | None = None
        for fig, fig_key in normalized_files:
            if fig in used:
                continue
            if desc_key in fig_key or fig_key in desc_key:
                matched = fig
                break
        if matched is not None:
            assignments.append((slot, matched))
            used.add(matched)

    remaining_slots = [slot for slot in slots if all(slot is not assigned[0] for assigned in assignments)]
    remaining_figures = [fig for fig in figures if fig not in used]
    assignments.extend(zip(remaining_slots, remaining_figures))
    return assignments


def embed_figures(input_docx: Path, output_docx: Path, figures: list[Path]) -> None:
    work = output_docx.with_suffix(".embed_tmp")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    with zipfile.ZipFile(input_docx, "r") as zf:
        zf.extractall(work)

    doc_path = work / "word" / "document.xml"
    rels_path = work / "word" / "_rels" / "document.xml.rels"
    ct_path = work / "[Content_Types].xml"
    media_dir = work / "word" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    parser = etree.XMLParser(remove_blank_text=False, recover=True)
    doc_tree = etree.parse(str(doc_path), parser)
    rels_tree = etree.parse(str(rels_path), parser)
    ct_tree = etree.parse(str(ct_path), parser)
    doc_root = doc_tree.getroot()
    rels_root = rels_tree.getroot()
    ensure_svg_content_type(ct_tree.getroot())

    slots = placeholder_slots(doc_root)
    assignments = assign_figures_to_slots(slots, [fig.resolve() for fig in figures])
    for i, (slot, fig) in enumerate(assignments, start=1):
        target_name = f"generated_fig_{i}{fig.suffix.lower()}"
        shutil.copy(fig, media_dir / target_name)
        rid = next_rid(rels_root)
        rel = etree.SubElement(rels_root, qn(REL_NS, "Relationship"))
        rel.set("Id", rid)
        rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
        rel.set("Target", f"media/{target_name}")
        para = slot["para"]
        parent = para.getparent()
        parent.replace(para, drawing_para(rid, target_name))

    doc_tree.write(str(doc_path), encoding="UTF-8", xml_declaration=True, standalone=True)
    rels_tree.write(str(rels_path), encoding="UTF-8", xml_declaration=True, standalone=True)
    ct_tree.write(str(ct_path), encoding="UTF-8", xml_declaration=True, standalone=True)

    if output_docx.exists():
        output_docx.unlink()
    with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in work.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(work).as_posix())
    shutil.rmtree(work)
    print(output_docx)


def main() -> int:
    ap = argparse.ArgumentParser(description="Replace Word image placeholders with generated SVG figure files.")
    ap.add_argument("input_docx")
    ap.add_argument("output_docx")
    ap.add_argument("figures", nargs="+")
    args = ap.parse_args()
    embed_figures(Path(args.input_docx), Path(args.output_docx), [Path(p) for p in args.figures])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
