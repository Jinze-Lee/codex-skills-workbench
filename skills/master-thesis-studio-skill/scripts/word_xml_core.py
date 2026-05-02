from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import re
from typing import Any

from lxml import etree

PKG_NS = "http://schemas.microsoft.com/office/2006/xmlPackage"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
V_NS = "urn:schemas-microsoft-com:vml"
RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

NS = {
    "pkg": PKG_NS,
    "w": W_NS,
    "r": R_NS,
    "m": M_NS,
    "v": V_NS,
    "rels": RELS_NS,
}

FRONT_KEYS = {"摘要", "摘 要", "ABSTRACT", "目录", "目 录"}
LOT_KEY = "表格目录"
LOF_KEY = "插图目录"
HEADING_PREFIX_RE = re.compile(
    r"^(?:第[零〇一二三四五六七八九十百\d]+章|第\s*\d+\s*章|[\d]+(?:\.[\d]+)*)(?:[、.．\s]+)?"
)

_GLOBAL_ID = 80000


def qn(ns: str, local: str) -> str:
    return f"{{{ns}}}{local}"


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def parser() -> etree.XMLParser:
    return etree.XMLParser(remove_blank_text=False, recover=True, huge_tree=True)


def read_xml_tree(xml_path: str | Path) -> etree._ElementTree:
    return etree.parse(str(Path(xml_path).resolve()), parser())


def require_flat_opc_root(tree_or_root: etree._ElementTree | etree._Element) -> etree._Element:
    root = tree_or_root.getroot() if isinstance(tree_or_root, etree._ElementTree) else tree_or_root
    if etree.QName(root).localname != "package" or root.nsmap.get(root.prefix) != PKG_NS:
        if root.tag != qn(PKG_NS, "package"):
            raise ValueError("Input XML is not Flat OPC / pkg:package")
    return root


def write_xml_tree(tree: etree._ElementTree, xml_path: str | Path) -> None:
    Path(xml_path).resolve().write_bytes(
        etree.tostring(
            tree,
            encoding="UTF-8",
            xml_declaration=True,
            standalone=True,
        )
    )


def get_attr(el: etree._Element | None, ns: str, local: str) -> str | None:
    if el is None:
        return None
    return el.get(qn(ns, local)) or el.get(local) or el.get(f"w:{local}")


def get_child(parent: etree._Element | None, ns: str, local: str) -> etree._Element | None:
    if parent is None:
        return None
    child = parent.find(f"{{{ns}}}{local}")
    if child is not None:
        return child
    for candidate in parent:
        if etree.QName(candidate).localname == local and candidate.nsmap.get(candidate.prefix) == ns:
            return candidate
    return None


def get_pkg_part(root: etree._Element, name: str) -> etree._Element | None:
    for part in root.findall("pkg:part", namespaces=NS):
        if part.get(qn(PKG_NS, "name")) == name:
            return part
    return None


def get_part_xml_root(part: etree._Element | None) -> etree._Element | None:
    if part is None:
        return None
    xml_data = part.find("pkg:xmlData", namespaces=NS)
    if xml_data is None or len(xml_data) == 0:
        return None
    return xml_data[0]


def get_body(root: etree._Element) -> etree._Element:
    doc_part = get_pkg_part(root, "/word/document.xml")
    doc_root = get_part_xml_root(doc_part)
    body = get_child(doc_root, W_NS, "body")
    if body is None:
        raise ValueError("Format error: /word/document.xml has no w:body")
    return body


def normalize_title(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\u3000", " ")).strip()


def normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").replace("\u3000", "")).strip()


def strip_heading_numbering(title: str) -> str:
    return HEADING_PREFIX_RE.sub("", title or "").strip()


def strip_ref_prefix(desc: str) -> str:
    return re.sub(r"^(\[\d+\]|\d+\.|Reference \d+)\s*", "", desc or "", flags=re.I).strip()


def para_text(p: etree._Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", namespaces=NS))


def instr_texts(p: etree._Element) -> list[str]:
    return [
        re.sub(r"\s+", " ", node.text or "").strip()
        for node in p.findall(".//w:instrText", namespaces=NS)
        if re.sub(r"\s+", " ", node.text or "").strip()
    ]


def bookmark_names(node: etree._Element) -> list[str]:
    return [
        name
        for bm in node.findall(".//w:bookmarkStart", namespaces=NS)
        if (name := get_attr(bm, W_NS, "name"))
    ]


def extract_style_id(p: etree._Element) -> str | None:
    p_pr = get_child(p, W_NS, "pPr")
    p_style = get_child(p_pr, W_NS, "pStyle")
    return get_attr(p_style, W_NS, "val")


def has_omml(p: etree._Element) -> bool:
    return bool(p.findall(".//m:oMath", namespaces=NS) or p.findall(".//m:oMathPara", namespaces=NS))


def strip_extracted_equation_number(text: str) -> str:
    value = normalize_title(text)
    value = re.sub(r"\s*#\s*[\(（]\s*\d+(?:[.．-]\d+)*\s*[\)）]\s*$", "", value)
    return value.strip()


def omml_text(node: etree._Element) -> str:
    return strip_extracted_equation_number("".join(t.text or "" for t in node.findall(".//m:t", namespaces=NS)))


def paragraph_markdown_with_math(p: etree._Element) -> str:
    parts: list[str] = []
    for child in p:
        child_name = etree.QName(child).localname
        child_ns = etree.QName(child).namespace
        if child_ns == W_NS and child_name == "r":
            text = "".join(t.text or "" for t in child.findall(".//w:t", namespaces=NS))
            if text:
                parts.append(text)
        elif child_ns == M_NS and child_name == "oMath":
            expr = omml_text(child)
            if expr:
                parts.append(f"[[SYM:{expr}]]")
        elif child_ns == M_NS and child_name == "oMathPara":
            expr = omml_text(child)
            if expr:
                parts.append(f"[[EQ:{expr}]]")
    if not parts:
        expr = omml_text(p)
        return f"[[EQ:{expr}]]" if expr else ""
    return cleanup_spacing("".join(parts)).strip()


def has_image_like(p: etree._Element) -> bool:
    return bool(
        p.findall(".//w:drawing", namespaces=NS)
        or p.findall(".//w:pict", namespaces=NS)
        or p.findall(".//v:shape", namespaces=NS)
    )


def has_field_seq(p: etree._Element) -> bool:
    return any(re.search(r"\bSEQ\b", text) for text in instr_texts(p))


def section_properties(node: etree._Element) -> etree._Element | None:
    local = etree.QName(node).localname
    if local == "sectPr":
        return node
    if local == "p":
        return node.find("./w:pPr/w:sectPr", namespaces=NS)
    return None


def is_section_break_node(node: etree._Element) -> bool:
    return section_properties(node) is not None


def is_front_matter_title(text: str) -> bool:
    t = normalize_for_match(text).lower()
    return t in {"摘要", "abstract", "目录", "插图目录", "表格目录"}


def is_back_matter_title(text: str) -> bool:
    t = normalize_for_match(text)
    return (
        t in {"致谢", "参考文献", "作者简介", "附录"}
        or re.match(r"^攻读.*期间.*发表", t) is not None
    )


def is_list_of_tables_title(text: str) -> bool:
    return normalize_for_match(text) == normalize_for_match(LOT_KEY)


def is_list_of_figures_title(text: str) -> bool:
    return normalize_for_match(text) == normalize_for_match(LOF_KEY)


def build_heading_styles(styles_root: etree._Element | None) -> dict[int, str]:
    if styles_root is None:
        return {1: "Heading1", 2: "Heading2", 3: "Heading3"}

    candidates: dict[int, list[dict[str, str]]] = {1: [], 2: [], 3: []}
    for style in styles_root.findall(".//w:style", namespaces=NS):
        if get_attr(style, W_NS, "type") != "paragraph":
            continue
        style_id = get_attr(style, W_NS, "styleId")
        if not style_id:
            continue
        name_node = get_child(style, W_NS, "name")
        name_val = get_attr(name_node, W_NS, "val") or ""
        outline = style.find("./w:pPr/w:outlineLvl", namespaces=NS)
        if outline is None:
            continue
        value = get_attr(outline, W_NS, "val")
        try:
            level = int(value or "") + 1
        except ValueError:
            continue
        if 1 <= level <= 3:
            candidates[level].append({"id": style_id, "name": name_val})

    def pick(level: int, fallback: str) -> str:
        items = candidates.get(level) or []
        if not items:
            return fallback
        for item in items:
            name = item["name"].lower()
            if (
                f"heading {level}" in name
                or f"heading{level}" in name
                or f"标题 {level}" in name
                or f"标题{level}" in name
            ):
                return item["id"]
        for item in items:
            style_id = item["id"].lower()
            if style_id in {str(level), f"heading{level}"} or f"heading{level}" in style_id:
                return item["id"]
        return items[0]["id"]

    return {1: pick(1, "Heading1"), 2: pick(2, "Heading2"), 3: pick(3, "Heading3")}


def style_name_by_id(styles_root: etree._Element | None, style_id: str) -> str:
    if styles_root is None:
        return style_id
    for style in styles_root.findall(".//w:style", namespaces=NS):
        if get_attr(style, W_NS, "styleId") == style_id:
            name_node = get_child(style, W_NS, "name")
            return get_attr(name_node, W_NS, "val") or style_id
    return style_id


def get_styles_root(root: etree._Element) -> etree._Element | None:
    return get_part_xml_root(get_pkg_part(root, "/word/styles.xml"))


def next_global_id() -> str:
    global _GLOBAL_ID
    _GLOBAL_ID += 1
    return str(_GLOBAL_ID)


def first_present(*nodes: etree._Element | None) -> etree._Element | None:
    for node in nodes:
        if node is not None:
            return node
    return None


def set_paragraph_alignment(p: etree._Element, value: str) -> None:
    p_pr = get_child(p, W_NS, "pPr")
    if p_pr is None:
        p_pr = etree.Element(qn(W_NS, "pPr"))
        p.insert(0, p_pr)
    jc = get_child(p_pr, W_NS, "jc")
    if jc is None:
        jc = etree.SubElement(p_pr, qn(W_NS, "jc"))
    jc.set(qn(W_NS, "val"), value)


def cleanup_spacing(text: str) -> str:
    if not text:
        return ""
    parts = re.split(r"(\[\[[\s\S]*?\]\])", text)
    cleaned: list[str] = []
    for part in parts:
        if part.startswith("[[") and part.endswith("]]"):
            cleaned.append(part)
            continue
        part = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[A-Za-z0-9])", "", part)
        part = re.sub(r"(?<=[A-Za-z0-9])\s+(?=[\u4e00-\u9fff])", "", part)
        part = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[（(])", "", part)
        part = re.sub(r"(?<=[）)])\s+(?=[\u4e00-\u9fff])", "", part)
        cleaned.append(part)
    return "".join(cleaned)


def placeholder_id(raw: str) -> str:
    raw = (raw or "").strip()
    match = re.search(r"\|id=([^|\]]+)", raw)
    return match.group(1).strip() if match else raw


def placeholder_display_text(raw: str) -> str:
    parts = [part.strip() for part in (raw or "").split("|")]
    display = [part for part in parts if part and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*=.*", part)]
    return " | ".join(display).strip()


def resolve_visual_ref(keyword: str, mapping: dict[str, int], prefix: str, chapter_index: int) -> str:
    kw = (keyword or "").strip()
    if not kw:
        return f"{prefix}[?]"
    if kw in mapping:
        return f"{prefix}{chapter_index}-{mapping[kw]}"
    for key, idx in mapping.items():
        if key and (key in kw or kw in key):
            return f"{prefix}{chapter_index}-{idx}"
    return f"{prefix}[未匹配:{kw}]"


def render_visual_references_for_chapter(chapter: dict[str, Any], chapter_index: int) -> None:
    nodes = [chapter] + flatten_chapters(chapter.get("subsections") or [])
    fig_map: dict[str, int] = {}
    tbl_map: dict[str, int] = {}
    for node in nodes:
        content = node.get("content") or ""
        for match in re.finditer(r"\[\[FIG:(.*?)\]\]", content, flags=re.S):
            raw = match.group(1)
            for key in {placeholder_id(raw), placeholder_display_text(raw)}:
                if key and key not in fig_map:
                    fig_map[key] = len(fig_map) + 1
        for match in re.finditer(r"\[\[TBL:(.*?)\]\]", content, flags=re.S):
            raw = match.group(1)
            for key in {placeholder_id(raw), placeholder_display_text(raw)}:
                if key and key not in tbl_map:
                    tbl_map[key] = len(tbl_map) + 1

    for node in nodes:
        content = node.get("content") or ""
        content = re.sub(
            r"\[\[REF_FIG(?::(.*?))?\]\]",
            lambda m: resolve_visual_ref(m.group(1) or "", fig_map, "图", chapter_index),
            content,
            flags=re.S,
        )
        content = re.sub(
            r"\[\[REF_TBL(?::(.*?))?\]\]",
            lambda m: resolve_visual_ref(m.group(1) or "", tbl_map, "表", chapter_index),
            content,
            flags=re.S,
        )
        content = re.sub(r"图\s*图(?=\d|\[)", "图", content)
        content = re.sub(r"表\s*表(?=\d|\[)", "表", content)
        content = re.sub(r"如图\s*图(?=\d|\[)", "如图", content)
        content = re.sub(r"如表\s*表(?=\d|\[)", "如表", content)
        content = cleanup_spacing(content)
        node["content"] = content


def empty_para_except_ppr(p: etree._Element) -> etree._Element:
    p_pr = get_child(p, W_NS, "pPr")
    p_pr_copy = deepcopy(p_pr) if p_pr is not None else None
    for child in list(p):
        p.remove(child)
    if p_pr_copy is not None:
        p.append(p_pr_copy)
    return p


def remove_paragraph_numbering(p: etree._Element) -> None:
    """Drop direct list numbering while keeping the paragraph style/layout."""
    p_pr = get_child(p, W_NS, "pPr")
    if p_pr is None:
        return
    num_pr = get_child(p_pr, W_NS, "numPr")
    if num_pr is not None:
        p_pr.remove(num_pr)


def has_paragraph_numbering(p: etree._Element | None) -> bool:
    p_pr = get_child(p, W_NS, "pPr")
    return get_child(p_pr, W_NS, "numPr") is not None


def reference_bookmark_name(ref_id: int | str) -> str:
    try:
        value = int(ref_id)
    except (TypeError, ValueError):
        value = sum((i + 1) * ord(ch) for i, ch in enumerate(str(ref_id))) % 100000
    return f"_Ref{120000 + value}"


def sample_run_from(proto: etree._Element | None) -> etree._Element:
    if proto is not None:
        found = proto.find(".//w:r", namespaces=NS)
        if found is not None:
            return deepcopy(found)
    run = etree.Element(qn(W_NS, "r"), nsmap={"w": W_NS})
    etree.SubElement(run, qn(W_NS, "rPr"))
    return run


def clean_run(sample_run: etree._Element, text: str = "", superscript: bool = False) -> etree._Element:
    run = deepcopy(sample_run)
    r_pr = get_child(run, W_NS, "rPr")
    r_pr_copy = deepcopy(r_pr) if r_pr is not None else etree.Element(qn(W_NS, "rPr"))
    for child in list(run):
        run.remove(child)
    if superscript:
        vert = etree.SubElement(r_pr_copy, qn(W_NS, "vertAlign"))
        vert.set(qn(W_NS, "val"), "superscript")
    run.append(r_pr_copy)
    t = etree.SubElement(run, qn(W_NS, "t"))
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    return run


def clone_para_with_text(proto: etree._Element, text: str) -> etree._Element:
    p = empty_para_except_ppr(deepcopy(proto))
    p.append(clean_run(sample_run_from(proto), text))
    return p


def table_rows_for_desc(desc: str) -> list[list[str]]:
    if "评价指标" in desc or "指标说明" in desc:
        return [
            ["指标", "含义", "用途"],
            ["Dice", "预测掩膜与真实掩膜的重叠程度", "主体精度评价"],
            ["IoU", "交集与并集之比", "区域重叠评价"],
            ["Sensitivity", "真实肿瘤区域被正确检出的比例", "小病灶检出评价"],
            ["HD95", "预测边界与真实边界的95% Hausdorff距离", "边界误差评价"],
        ]
    if "训练参数" in desc:
        return [
            ["参数", "设置"],
            ["输入尺寸", "256 x 256"],
            ["Batch size", "8"],
            ["训练轮数", "120"],
            ["优化器", "AdamW"],
            ["初始学习率", "0.0003"],
            ["损失函数", "Dice Loss + BCE Loss"],
        ]
    if "环境配置" in desc:
        return [
            ["项目", "配置"],
            ["操作系统", "Ubuntu 20.04"],
            ["Python", "3.10"],
            ["PyTorch", "2.1"],
            ["CUDA", "11.8"],
            ["GPU", "RTX 3060 12GB"],
        ]
    if "性能对比" in desc or "模型性能" in desc:
        return [
            ["模型", "Dice/%", "IoU/%", "Sensitivity/%", "HD95"],
            ["U-Net", "86.4", "76.1", "84.7", "9.8"],
            ["Attention U-Net", "88.1", "78.9", "86.5", "8.6"],
            ["Att-TumorNet", "90.3", "82.4", "89.2", "6.9"],
        ]
    if "消融" in desc:
        return [
            ["设置", "Dice/%", "说明"],
            ["Baseline", "86.4", "U-Net主干"],
            ["+ Channel Attention", "87.6", "增强通道特征选择"],
            ["+ Spatial Attention", "88.2", "增强区域定位"],
            ["+ Dual Attention", "90.3", "通道与空间联合建模"],
        ]
    return [["项目", "内容"], [desc or "表格", "待补充"]]


def table_style_id_from_template(template_table: etree._Element | None) -> str | None:
    if template_table is None:
        return None
    style = template_table.find("./w:tblPr/w:tblStyle", namespaces=NS)
    return get_attr(style, W_NS, "val") if style is not None else None


def add_border(parent: etree._Element, side: str, val: str, sz: str = "0", color: str = "auto") -> etree._Element:
    border = etree.SubElement(parent, qn(W_NS, side))
    border.set(qn(W_NS, "val"), val)
    border.set(qn(W_NS, "sz"), sz)
    border.set(qn(W_NS, "space"), "0")
    border.set(qn(W_NS, "color"), color)
    return border


def add_three_line_table_borders(tbl_pr: etree._Element) -> None:
    borders = etree.SubElement(tbl_pr, qn(W_NS, "tblBorders"))
    add_border(borders, "top", "single", "12")
    add_border(borders, "left", "none", "0")
    add_border(borders, "bottom", "single", "12")
    add_border(borders, "right", "none", "0")
    add_border(borders, "insideH", "none", "0")
    add_border(borders, "insideV", "none", "0")


def add_header_cell_bottom_border(tc_pr: etree._Element) -> None:
    borders = etree.SubElement(tc_pr, qn(W_NS, "tcBorders"))
    add_border(borders, "bottom", "single", "4")


def set_table_cell_vertical_alignment(tc_pr: etree._Element, value: str = "center") -> None:
    valign = get_child(tc_pr, W_NS, "vAlign")
    if valign is None:
        valign = etree.SubElement(tc_pr, qn(W_NS, "vAlign"))
    valign.set(qn(W_NS, "val"), value)


def create_simple_table(
    rows: list[list[str]],
    sample_run: etree._Element,
    template_table: etree._Element | None = None,
) -> etree._Element:
    col_count = max((len(row) for row in rows), default=1)
    tbl = etree.Element(qn(W_NS, "tbl"))
    tbl_pr = etree.SubElement(tbl, qn(W_NS, "tblPr"))
    style_id = table_style_id_from_template(template_table)
    if style_id:
        tbl_style = etree.SubElement(tbl_pr, qn(W_NS, "tblStyle"))
        tbl_style.set(qn(W_NS, "val"), style_id)
    tbl_w = etree.SubElement(tbl_pr, qn(W_NS, "tblW"))
    tbl_w.set(qn(W_NS, "w"), "0")
    tbl_w.set(qn(W_NS, "type"), "auto")
    jc = etree.SubElement(tbl_pr, qn(W_NS, "jc"))
    jc.set(qn(W_NS, "val"), "center")
    add_three_line_table_borders(tbl_pr)
    grid = etree.SubElement(tbl, qn(W_NS, "tblGrid"))
    for _ in range(col_count):
        col = etree.SubElement(grid, qn(W_NS, "gridCol"))
        col.set(qn(W_NS, "w"), str(max(1500, 9000 // col_count)))
    for row_index, row in enumerate(rows):
        tr = etree.SubElement(tbl, qn(W_NS, "tr"))
        for value in row + [""] * (col_count - len(row)):
            tc = etree.SubElement(tr, qn(W_NS, "tc"))
            tc_pr = etree.SubElement(tc, qn(W_NS, "tcPr"))
            tc_w = etree.SubElement(tc_pr, qn(W_NS, "tcW"))
            tc_w.set(qn(W_NS, "w"), str(max(1500, 9000 // col_count)))
            tc_w.set(qn(W_NS, "type"), "dxa")
            set_table_cell_vertical_alignment(tc_pr)
            if row_index == 0:
                add_header_cell_bottom_border(tc_pr)
            p = etree.SubElement(tc, qn(W_NS, "p"))
            set_paragraph_alignment(p, "center")
            p.append(clean_run(sample_run, value))
    return tbl


def create_field_runs(sample_run: etree._Element, instr: str, display: str, superscript: bool = False) -> list[etree._Element]:
    def fld(kind: str) -> etree._Element:
        run = deepcopy(sample_run)
        r_pr = get_child(run, W_NS, "rPr")
        r_pr_copy = deepcopy(r_pr) if r_pr is not None else etree.Element(qn(W_NS, "rPr"))
        for child in list(run):
            run.remove(child)
        if superscript:
            vert = etree.SubElement(r_pr_copy, qn(W_NS, "vertAlign"))
            vert.set(qn(W_NS, "val"), "superscript")
        run.append(r_pr_copy)
        char = etree.SubElement(run, qn(W_NS, "fldChar"))
        char.set(qn(W_NS, "fldCharType"), kind)
        return run

    def instr_run() -> etree._Element:
        run = deepcopy(sample_run)
        r_pr = get_child(run, W_NS, "rPr")
        r_pr_copy = deepcopy(r_pr) if r_pr is not None else etree.Element(qn(W_NS, "rPr"))
        for child in list(run):
            run.remove(child)
        if superscript:
            vert = etree.SubElement(r_pr_copy, qn(W_NS, "vertAlign"))
            vert.set(qn(W_NS, "val"), "superscript")
        run.append(r_pr_copy)
        node = etree.SubElement(run, qn(W_NS, "instrText"))
        node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        node.text = instr
        return run

    return [
        fld("begin"),
        instr_run(),
        fld("separate"),
        clean_run(sample_run, display, superscript=superscript),
        fld("end"),
    ]


def create_bookmark(name: str, bm_id: str, start: bool) -> etree._Element:
    tag = "bookmarkStart" if start else "bookmarkEnd"
    node = etree.Element(qn(W_NS, tag), nsmap={"w": W_NS})
    node.set(qn(W_NS, "id"), bm_id)
    if start:
        node.set(qn(W_NS, "name"), name)
    return node


LATEX_SYMBOLS = {
    r"\in": "∈",
    r"\times": "×",
    r"\cap": "∩",
    r"\cup": "∪",
    r"\otimes": "⊗",
    r"\sigma": "σ",
    r"\lambda": "λ",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\epsilon": "ε",
    r"\theta": "θ",
    r"\mu": "μ",
    r"\sum": "∑",
    r"\leq": "≤",
    r"\geq": "≥",
    r"\neq": "≠",
    r"\approx": "≈",
}


def normalize_latex_math_text(text: str) -> str:
    value = text or ""
    value = re.sub(r"\\mathbb\s*\{\s*R\s*\}", "ℝ", value)
    value = re.sub(r"\\mathbb\s*R", "ℝ", value)
    value = value.replace(r"\left", "").replace(r"\right", "")
    value = value.replace(r"\{", "{").replace(r"\}", "}")
    value = value.replace(r"\,", " ").replace(r"\;", " ").replace(r"\quad", " ")
    for latex, symbol in sorted(LATEX_SYMBOLS.items(), key=lambda item: len(item[0]), reverse=True):
        value = value.replace(latex, symbol)
    value = re.sub(r"(?<=∈)\s*R(?=\s*(?:\^|$))", "ℝ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\s*([∈×∩∪⊗=+\-])\s*", r"\1", value)
    return value


def consume_braced(text: str, start: int) -> tuple[str, int]:
    i = start
    while i < len(text) and text[i].isspace():
        i += 1
    if i >= len(text) or text[i] != "{":
        return "", i
    depth = 0
    out: list[str] = []
    while i < len(text):
        char = text[i]
        if char == "{" and (i == 0 or text[i - 1] != "\\"):
            depth += 1
            if depth > 1:
                out.append(char)
        elif char == "}" and (i == 0 or text[i - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return "".join(out), i + 1
            out.append(char)
        else:
            out.append(char)
        i += 1
    return "".join(out), i


def split_base_for_script(buffer: str) -> tuple[str, str]:
    if not buffer:
        return "", ""
    end = len(buffer)
    while end > 0 and buffer[end - 1].isspace():
        end -= 1
    trailing = buffer[end:]
    if end == 0:
        return buffer, ""
    if buffer[end - 1] == "}":
        depth = 0
        for i in range(end - 1, -1, -1):
            char = buffer[i]
            if char == "}":
                depth += 1
            elif char == "{":
                depth -= 1
                if depth == 0:
                    return buffer[:i] + trailing, buffer[i:end]
    return buffer[: end - 1] + trailing, buffer[end - 1 : end]


def create_math_text_run(text: str) -> etree._Element:
    m_run = etree.Element(qn(M_NS, "r"), nsmap={"m": M_NS, "w": W_NS})
    m_rpr = etree.SubElement(m_run, qn(M_NS, "rPr"))
    sty = etree.SubElement(m_rpr, qn(M_NS, "sty"))
    sty.set(qn(M_NS, "val"), "p")
    w_rpr = etree.SubElement(m_run, qn(W_NS, "rPr"))
    fonts = etree.SubElement(w_rpr, qn(W_NS, "rFonts"))
    fonts.set(qn(W_NS, "ascii"), "Cambria Math")
    fonts.set(qn(W_NS, "hAnsi"), "Cambria Math")
    t = etree.SubElement(m_run, qn(M_NS, "t"))
    t.text = text
    return m_run


def append_math_children(parent: etree._Element, expression: str) -> None:
    for node in create_math_nodes(expression):
        parent.append(node)


def create_script_node(kind: str, base: str, script: str) -> etree._Element:
    tag = "sSup" if kind == "^" else "sSub"
    script_tag = "sup" if kind == "^" else "sub"
    node = etree.Element(qn(M_NS, tag), nsmap={"m": M_NS, "w": W_NS})
    e = etree.SubElement(node, qn(M_NS, "e"))
    append_math_children(e, base)
    script_node = etree.SubElement(node, qn(M_NS, script_tag))
    append_math_children(script_node, script)
    return node


def create_fraction_node(num_text: str, den_text: str) -> etree._Element:
    node = etree.Element(qn(M_NS, "f"), nsmap={"m": M_NS, "w": W_NS})
    num = etree.SubElement(node, qn(M_NS, "num"))
    append_math_children(num, num_text)
    den = etree.SubElement(node, qn(M_NS, "den"))
    append_math_children(den, den_text)
    return node


def create_math_nodes(expression: str) -> list[etree._Element]:
    nodes: list[etree._Element] = []

    def flush_buffer(raw: str) -> None:
        text = normalize_latex_math_text(raw)
        if not text:
            return
        buffer = ""
        i = 0
        while i < len(text):
            char = text[i]
            if char in {"^", "_"}:
                before, base = split_base_for_script(buffer)
                if before:
                    nodes.append(create_math_text_run(before))
                buffer = ""
                if i + 1 < len(text) and text[i + 1] == "{":
                    script, next_i = consume_braced(text, i + 1)
                elif i + 1 < len(text):
                    script, next_i = text[i + 1], i + 2
                else:
                    script, next_i = "", i + 1
                if base:
                    nodes.append(create_script_node(char, base, script))
                else:
                    nodes.append(create_math_text_run(char + script))
                i = next_i
                continue
            buffer += char
            i += 1
        if buffer:
            nodes.append(create_math_text_run(buffer))

    i = 0
    buffer = ""
    while i < len(expression):
        if expression.startswith(r"\frac", i):
            flush_buffer(buffer)
            buffer = ""
            num, next_i = consume_braced(expression, i + len(r"\frac"))
            den, next_i = consume_braced(expression, next_i)
            nodes.append(create_fraction_node(num, den))
            i = next_i
            continue
        buffer += expression[i]
        i += 1
    flush_buffer(buffer)
    return nodes


@dataclass
class Prototypes:
    h1: etree._Element | None = None
    h2: etree._Element | None = None
    h3: etree._Element | None = None
    normal: etree._Element | None = None
    caption: etree._Element | None = None
    ref_entry: etree._Element | None = None
    table: etree._Element | None = None


def find_prototypes(body: etree._Element, heading_styles: dict[int, str]) -> Prototypes:
    protos = Prototypes()
    seen_ref_title = False
    for node in body:
        local = etree.QName(node).localname
        if local == "tbl" and protos.table is None:
            protos.table = node
            continue
        if local != "p":
            continue
        style_id = extract_style_id(node)
        text = para_text(node)
        normalized = normalize_for_match(text)
        if style_id == heading_styles.get(1) and protos.h1 is None and not is_front_matter_title(text) and not is_back_matter_title(text):
            protos.h1 = node
        elif style_id == heading_styles.get(2) and protos.h2 is None:
            protos.h2 = node
        elif style_id == heading_styles.get(3) and protos.h3 is None:
            protos.h3 = node

        if is_back_matter_title(text) and "参考文献" in normalized:
            seen_ref_title = True
        elif seen_ref_title and protos.ref_entry is None and text.strip():
            protos.ref_entry = node

        if has_field_seq(node) and protos.caption is None:
            protos.caption = node

        if (
            protos.normal is None
            and style_id not in {heading_styles.get(1), heading_styles.get(2), heading_styles.get(3)}
            and not has_field_seq(node)
            and not is_front_matter_title(text)
            and not is_back_matter_title(text)
            and len(text.strip()) > 5
        ):
            protos.normal = node

    if protos.h1 is None:
        protos.h1 = next((n for n in body if etree.QName(n).localname == "p" and extract_style_id(n) == heading_styles.get(1)), None)
    if protos.normal is None:
        protos.normal = next((n for n in body if etree.QName(n).localname == "p" and extract_style_id(n) is None), None)
    if protos.normal is None:
        protos.normal = next((n for n in body if etree.QName(n).localname == "p"), None)
    return protos


def apply_style_overrides(node: etree._Element, config: dict[str, Any] | None) -> None:
    if not config:
        return
    for run in node.findall(".//w:r", namespaces=NS):
        r_pr = get_child(run, W_NS, "rPr")
        if r_pr is None:
            r_pr = etree.Element(qn(W_NS, "rPr"))
            run.insert(0, r_pr)
        fonts = get_child(r_pr, W_NS, "rFonts")
        if fonts is None:
            fonts = etree.SubElement(r_pr, qn(W_NS, "rFonts"))
        fonts.set(qn(W_NS, "ascii"), config.get("fontFamilyAscii", "Times New Roman"))
        fonts.set(qn(W_NS, "hAnsi"), config.get("fontFamilyAscii", "Times New Roman"))
        fonts.set(qn(W_NS, "eastAsia"), config.get("fontFamilyCI", "SimSun"))
        fonts.set(qn(W_NS, "hint"), "eastAsia")
        for old in list(r_pr.findall("w:sz", namespaces=NS)) + list(r_pr.findall("w:szCs", namespaces=NS)):
            r_pr.remove(old)
        size = str(config.get("fontSize", "21"))
        sz = etree.SubElement(r_pr, qn(W_NS, "sz"))
        sz.set(qn(W_NS, "val"), size)
        sz_cs = etree.SubElement(r_pr, qn(W_NS, "szCs"))
        sz_cs.set(qn(W_NS, "val"), size)


def strip_inline_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text.strip()


def split_markdown_table_row(line: str) -> list[str]:
    return [strip_inline_markdown(cell) for cell in line.strip().strip("|").split("|")]


def is_markdown_table_separator(line: str) -> bool:
    cells = [cell.strip().replace(" ", "") for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def markdown_table_rows(chunk: str) -> list[list[str]]:
    lines = [line.strip() for line in chunk.splitlines() if line.strip()]
    if len(lines) < 2 or "|" not in lines[0] or not is_markdown_table_separator(lines[1]):
        return []
    rows = [split_markdown_table_row(lines[0])]
    for line in lines[2:]:
        if "|" in line:
            rows.append(split_markdown_table_row(line))
    return rows if len(rows) > 1 else []


def image_placeholder_text(desc: str) -> str:
    desc = normalize_title(desc)
    return f"（在此处插入图片：{desc}）" if desc else "（在此处插入图片）"


def caption_desc_from_text(text: str, label: str) -> str:
    value = normalize_title(text)
    if not value:
        return ""
    value = re.sub(rf"^{re.escape(label)}\s*", "", value)
    value = re.sub(r"^[\(（]?\s*[零〇一二三四五六七八九十百\d]+(?:[-.．]\d+)*(?:\s*[)）])?\s*", "", value)
    value = re.sub(r"^[\s:：、.．-]+", "", value)
    return value.strip() or normalize_title(text)


def caption_kind(node: etree._Element) -> str | None:
    if etree.QName(node).localname != "p":
        return None
    raw = normalize_title(para_text(node))
    text = normalize_for_match(raw)
    looks_like_caption = has_field_seq(node) or bool(re.match(r"^[图表]\s*[（(]?[零〇一二三四五六七八九十百\d]", raw))
    if not looks_like_caption:
        return None
    if "表" in text:
        return "table"
    if "图" in text:
        return "figure"
    return None


def caption_desc_for_kind(node: etree._Element, kind: str) -> str:
    label = "表" if kind == "table" else "图"
    return caption_desc_from_text(para_text(node), label)


def adjacent_caption_desc(nodes: list[etree._Element], index: int, kind: str) -> str:
    offsets = (1, -1) if kind == "figure" else (-1, 1)
    for offset in offsets:
        pos = index + offset
        if 0 <= pos < len(nodes):
            node = nodes[pos]
            if etree.QName(node).localname == "p" and caption_kind(node) == kind:
                return caption_desc_for_kind(node, kind)
    return ""


def table_cell_text(tc: etree._Element) -> str:
    parts = [cleanup_spacing(normalize_title(para_text(p))) for p in tc.findall("./w:p", namespaces=NS)]
    text = " ".join(part for part in parts if part)
    if text:
        return text
    return cleanup_spacing(normalize_title(para_text(tc)))


def markdown_table_from_rows(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    col_count = max((len(row) for row in rows), default=0)
    if col_count <= 0:
        return ""
    padded = [row + [""] * (col_count - len(row)) for row in rows]
    if len(padded) == 1:
        padded.append([""] * col_count)

    def fmt(row: list[str]) -> str:
        escaped = [cell.replace("|", r"\|") for cell in row]
        return "| " + " | ".join(escaped) + " |"

    lines = [fmt(padded[0]), "| " + " | ".join(["---"] * col_count) + " |"]
    lines.extend(fmt(row) for row in padded[1:])
    return "\n".join(lines)


def table_to_markdown(tbl: etree._Element) -> str:
    rows: list[list[str]] = []
    for tr in tbl.findall("./w:tr", namespaces=NS):
        row = [table_cell_text(tc) for tc in tr.findall("./w:tc", namespaces=NS)]
        if any(cell for cell in row):
            rows.append(row)
    return markdown_table_from_rows(rows)


def create_content_nodes(
    content_raw: str,
    protos: Prototypes,
    chapter_index: int,
    counters: dict[str, int],
    style_settings: dict[str, Any] | None = None,
) -> list[etree._Element]:
    if not content_raw:
        return []
    base_proto = first_present(protos.normal, protos.h1)
    if base_proto is None:
        return []
    sample_run = sample_run_from(base_proto)
    processed = re.sub(r"(\[\[(?:FIG|TBL|EQ):[\s\S]*?\]\])", r"\n\n\1\n\n", content_raw)
    chunks = [p.strip() for p in re.split(r"\n\s*\n", processed) if p.strip()]
    nodes: list[etree._Element] = []
    index = 0

    while index < len(chunks):
        chunk = chunks[index]
        if chunk.startswith("[[FIG:"):
            counters["fig"] += 1
            raw_desc = re.sub(r"^\[\[FIG:", "", chunk)
            raw_desc = re.sub(r"\]\]$", "", raw_desc).strip()
            desc = placeholder_display_text(raw_desc) or "图片"
            bm_id = next_global_id()
            bm_name = f"_Fig_{bm_id}"
            p_img = clone_para_with_text(base_proto, image_placeholder_text(desc))
            set_paragraph_alignment(p_img, "center")
            apply_style_overrides(p_img, (style_settings or {}).get("body"))
            nodes.append(p_img)

            p_cap = empty_para_except_ppr(deepcopy(first_present(protos.caption, base_proto)))
            set_paragraph_alignment(p_cap, "center")
            p_cap.append(create_bookmark(bm_name, bm_id, True))
            p_cap.append(clean_run(sample_run, "图 "))
            p_cap.append(clean_run(sample_run, f"{chapter_index}-"))
            for run in create_field_runs(sample_run, r"SEQ Figure \* ARABIC \s 1", str(counters["fig"])):
                p_cap.append(run)
            p_cap.append(create_bookmark(bm_name, bm_id, False))
            p_cap.append(clean_run(sample_run, "  " + desc))
            apply_style_overrides(p_cap, (style_settings or {}).get("caption"))
            nodes.append(p_cap)
            index += 1
            continue

        if chunk.startswith("[[TBL:"):
            counters["tbl"] += 1
            raw_desc = re.sub(r"^\[\[TBL:", "", chunk)
            raw_desc = re.sub(r"\]\]$", "", raw_desc).strip()
            desc = placeholder_display_text(raw_desc) or "表格"
            bm_id = next_global_id()
            bm_name = f"_Tbl_{bm_id}"
            p_cap = empty_para_except_ppr(deepcopy(first_present(protos.caption, base_proto)))
            set_paragraph_alignment(p_cap, "center")
            p_cap.append(create_bookmark(bm_name, bm_id, True))
            p_cap.append(clean_run(sample_run, "表 "))
            p_cap.append(clean_run(sample_run, f"{chapter_index}-"))
            for run in create_field_runs(sample_run, r"SEQ Table \* ARABIC \s 1", str(counters["tbl"])):
                p_cap.append(run)
            p_cap.append(create_bookmark(bm_name, bm_id, False))
            p_cap.append(clean_run(sample_run, "  " + desc))
            apply_style_overrides(p_cap, (style_settings or {}).get("caption"))
            nodes.append(p_cap)
            next_rows = markdown_table_rows(chunks[index + 1]) if index + 1 < len(chunks) else []
            rows = next_rows or table_rows_for_desc(desc)
            nodes.append(create_simple_table(rows, sample_run, protos.table))
            index += 2 if next_rows else 1
            continue

        table_rows = markdown_table_rows(chunk)
        if table_rows:
            nodes.append(create_simple_table(table_rows, sample_run, protos.table))
            index += 1
            continue

        if chunk.startswith("[[EQ:"):
            counters["eq"] += 1
            eq_text = re.sub(r"^\[\[EQ:", "", chunk)
            eq_text = re.sub(r"\]\]$", "", eq_text).strip()
            sep = (style_settings or {}).get("equationSeparator", ".")
            p_eq = empty_para_except_ppr(deepcopy(base_proto))
            o_math_para = etree.SubElement(p_eq, qn(M_NS, "oMathPara"))
            o_math = etree.SubElement(o_math_para, qn(M_NS, "oMath"))
            append_math_children(o_math, f"{eq_text}#({chapter_index}{sep}{counters['eq']})")
            nodes.append(p_eq)
            index += 1
            continue

        p = empty_para_except_ppr(deepcopy(base_proto))
        parts = re.split(r"(\[\[(?:SYM|REF):.*?\]\])", chunk)
        for part in parts:
            if not part:
                continue
            if part.startswith("[[SYM:"):
                sym = re.sub(r"^\[\[SYM:", "", part)
                sym = re.sub(r"\]\]$", "", sym)
                o_math = etree.SubElement(p, qn(M_NS, "oMath"))
                append_math_children(o_math, sym)
            elif re.match(r"^\[\[REF:\d+\]\]$", part):
                ref_id = re.search(r"\d+", part).group(0)  # type: ignore[union-attr]
                bm_name = reference_bookmark_name(ref_id)
                switch = "\\r \\h" if has_paragraph_numbering(protos.ref_entry) else "\\h"
                for run in create_field_runs(sample_run, f" REF {bm_name} {switch} ", f"[{ref_id}]", superscript=True):
                    p.append(run)
            else:
                p.append(clean_run(sample_run, part))
        apply_style_overrides(p, (style_settings or {}).get("body"))
        nodes.append(p)
        index += 1

    return nodes


def extract_chapters_from_root(root: etree._Element) -> dict[str, Any]:
    styles_root = get_styles_root(root)
    heading_styles = build_heading_styles(styles_root)
    body = get_body(root)
    chapters: list[dict[str, Any]] = []
    current_l1: dict[str, Any] | None = None
    current_l2: dict[str, Any] | None = None
    current_l3: dict[str, Any] | None = None
    preview = ""
    index = 0

    def target() -> dict[str, Any] | None:
        return current_l3 or current_l2 or current_l1

    body_nodes = [node for node in body if etree.QName(node).localname in {"p", "tbl"}]
    idx = 0
    while idx < len(body_nodes):
        node = body_nodes[idx]
        local = etree.QName(node).localname
        text = para_text(node).strip() if local == "p" else ""
        style_id = extract_style_id(node) if local == "p" else None
        if style_id == heading_styles.get(1) and text:
            index += 1
            current_l1 = {"id": f"ch_{index}", "title": text, "level": 1, "content": "", "subsections": []}
            chapters.append(current_l1)
            current_l2 = None
            current_l3 = None
            idx += 1
        elif style_id == heading_styles.get(2) and text and current_l1 is not None:
            index += 1
            current_l2 = {"id": f"sec_{index}", "title": text, "level": 2, "content": "", "subsections": []}
            current_l1["subsections"].append(current_l2)
            current_l3 = None
            idx += 1
        elif style_id == heading_styles.get(3) and text and current_l2 is not None:
            index += 1
            current_l3 = {"id": f"sub_{index}", "title": text, "level": 3, "content": "", "subsections": []}
            current_l2["subsections"].append(current_l3)
            idx += 1
        else:
            active = target()
            if active is None:
                idx += 1
                continue
            if local == "p":
                kind = caption_kind(node)
                prev_is_image = idx > 0 and etree.QName(body_nodes[idx - 1]).localname == "p" and has_image_like(body_nodes[idx - 1])
                next_is_image = (
                    idx + 1 < len(body_nodes)
                    and etree.QName(body_nodes[idx + 1]).localname == "p"
                    and has_image_like(body_nodes[idx + 1])
                )
                next_is_table = idx + 1 < len(body_nodes) and etree.QName(body_nodes[idx + 1]).localname == "tbl"
                if (kind == "figure" and (prev_is_image or next_is_image)) or (kind == "table" and next_is_table):
                    idx += 1
                    continue
            if local == "tbl":
                desc = adjacent_caption_desc(body_nodes, idx, "table") or "包含一个表格"
                active["content"] += f"\n\n[[TBL:{desc}]]\n\n"
                md_table = table_to_markdown(node)
                if md_table:
                    active["content"] += md_table + "\n\n"
            elif local == "p" and has_image_like(node):
                desc = adjacent_caption_desc(body_nodes, idx, "figure") or "包含图片"
                active["content"] += f"\n\n[[FIG:{desc}]]\n\n"
                idx += 1
                continue
            elif local == "p" and has_omml(node):
                math_md = paragraph_markdown_with_math(node)
                if math_md:
                    active["content"] += f"\n\n{math_md}\n\n"
                if text and len(preview) < 2000:
                    preview += text + " "
            elif text:
                active["content"] += text + "\n\n"
                if len(preview) < 2000:
                    preview += text + " "
            idx += 1

    return {
        "chapters": chapters,
        "rawTextPreview": preview[:2000],
        "headingStyleIds": {
            "h1": heading_styles.get(1),
            "h2": heading_styles.get(2),
            "h3": heading_styles.get(3),
        },
    }


def classify_block(node: etree._Element, heading_styles: dict[int, str]) -> tuple[str, int]:
    local = etree.QName(node).localname
    if local == "tbl":
        return "table", 0
    if local == "sectPr":
        return "other", 0
    if local != "p":
        return "other", 0
    text = para_text(node).strip()
    style_id = extract_style_id(node)
    if style_id == heading_styles.get(1):
        return "heading", 1
    if style_id == heading_styles.get(2):
        return "heading", 2
    if style_id == heading_styles.get(3):
        return "heading", 3
    if is_front_matter_title(text):
        return "front_title", 1
    if is_back_matter_title(text):
        return "back_title", 1
    if is_list_of_tables_title(text) or is_list_of_figures_title(text):
        return "toc_title", 1
    if has_image_like(node):
        return "image_placeholder", 0
    if has_omml(node):
        return "equation", 0
    if has_field_seq(node):
        if "表" in text:
            return "caption_table", 0
        return "caption_figure", 0
    return "paragraph", 0


def extract_mapping(root: etree._Element, source: str = "template.flat.xml") -> dict[str, Any]:
    styles_root = get_styles_root(root)
    heading_styles = build_heading_styles(styles_root)
    body = get_body(root)
    sections: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    current = {
        "id": f"sec_{next_global_id()}",
        "kind": "front",
        "title": "Front Matter",
        "level": 0,
        "startOrder": 0,
        "endOrder": 0,
        "blocks": [],
    }
    sections.append(current)
    for order, node in enumerate(body, start=1):
        local = etree.QName(node).localname
        if local not in {"p", "tbl", "sectPr"}:
            continue
        kind, level = classify_block(node, heading_styles)
        text = normalize_title(para_text(node)) if local == "p" else ""
        if kind in {"heading", "front_title", "back_title", "toc_title"}:
            section_kind = "body" if kind == "heading" else "front"
            if kind == "back_title":
                section_kind = "back"
            elif kind == "toc_title" or "目录" in text:
                section_kind = "toc"
            current = {
                "id": f"sec_{next_global_id()}",
                "kind": section_kind,
                "title": text or kind,
                "level": level,
                "startOrder": order,
                "endOrder": order,
                "blocks": [],
            }
            sections.append(current)
        block_id = f"blk_{next_global_id()}"
        block = {
            "id": block_id,
            "order": order,
            "nodeType": local,
            "type": kind,
            "level": level,
            "styleId": extract_style_id(node) if local == "p" else None,
            "text": text,
            "owner": {"sectionId": current["id"]},
            "fields": instr_texts(node) if local == "p" else [],
            "bookmarks": bookmark_names(node),
        }
        blocks.append(block)
        current["blocks"].append(block_id)
        current["endOrder"] = order
    return {
        "source": source,
        "headingStyleIds": {
            "h1": heading_styles.get(1),
            "h2": heading_styles.get(2),
            "h3": heading_styles.get(3),
        },
        "sections": sections,
        "blocks": blocks,
    }


def parse_template_xml(xml_path: str | Path) -> dict[str, Any]:
    tree = read_xml_tree(xml_path)
    root = require_flat_opc_root(tree)
    styles_root = get_styles_root(root)
    mapping = extract_mapping(root, Path(xml_path).name)
    extracted = extract_chapters_from_root(root)
    return {
        "source": str(Path(xml_path).resolve()),
        "has_document_xml": get_pkg_part(root, "/word/document.xml") is not None,
        "has_styles_xml": get_pkg_part(root, "/word/styles.xml") is not None,
        "has_document_rels": get_pkg_part(root, "/word/_rels/document.xml.rels") is not None,
        "style_count": len(styles_root.findall(".//w:style", namespaces=NS)) if styles_root is not None else 0,
        "headingStyleIds": mapping["headingStyleIds"],
        "chapters": extracted["chapters"],
        "rawTextPreview": extracted["rawTextPreview"],
        "mapping": mapping,
    }


def doc_relationships(root: etree._Element) -> dict[str, str]:
    rels_root = get_part_xml_root(get_pkg_part(root, "/word/_rels/document.xml.rels"))
    if rels_root is None:
        return {}
    result: dict[str, str] = {}
    for rel in rels_root.findall(".//rels:Relationship", namespaces=NS):
        rel_id = rel.get("Id")
        target = rel.get("Target")
        if rel_id and target:
            result[rel_id] = target
    return result


def chinese_chapter_number(index: int) -> str:
    digits = "\u96f6\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d"
    if index <= 0:
        return str(index)
    if index < 10:
        return digits[index]
    if index == 10:
        return "\u5341"
    if index < 20:
        return "\u5341" + digits[index - 10]
    tens, ones = divmod(index, 10)
    return digits[tens] + "\u5341" + (digits[ones] if ones else "")


def chapter_header_cache_text(chapters: list[dict[str, Any]]) -> str | None:
    level_one = [ch for ch in chapters if int(ch.get("level") or 1) == 1] or chapters
    if not level_one:
        return None
    title = strip_heading_numbering(level_one[0].get("title") or "")
    return f"\u7b2c{chinese_chapter_number(1)}\u7ae0 {title}".strip()


def update_styleref_cached_text(xml_root: etree._Element, target_style: str, cached_text: str | None) -> None:
    if not cached_text:
        return
    no_number_heading = "\u65e0\u7f16\u53f7\u6807\u9898"
    for paragraph in xml_root.findall(".//w:p", namespaces=NS):
        instrs = instr_texts(paragraph)
        instr = "".join(instrs)
        normalized_instr = normalize_for_match(instr)
        if "STYLEREF" not in instr or no_number_heading in normalized_instr or "TOC" in normalized_instr.upper():
            continue
        text_nodes = paragraph.findall(".//w:t", namespaces=NS)
        if not text_nodes:
            continue
        text_nodes[0].text = cached_text
        for node in text_nodes[1:]:
            node.text = ""


def update_headers_and_footers(
    root: etree._Element,
    h1_style_name: str,
    style_settings: dict[str, Any] | None = None,
    chapter_cache_text: str | None = None,
) -> None:
    settings = style_settings or {}
    header = settings.get("header") or {}
    target_style = header.get("headerReferenceStyle") or h1_style_name or "\u6807\u9898 1"
    for part in root.findall("pkg:part", namespaces=NS):
        name = part.get(qn(PKG_NS, "name")) or ""
        if "/word/header" not in name and "/word/footer" not in name:
            continue
        xml_root = get_part_xml_root(part)
        if xml_root is None:
            continue
        for instr in xml_root.findall(".//w:instrText", namespaces=NS):
            text = instr.text or ""
            if "STYLEREF" in text and header.get("oddPage") == "chapterTitle":
                instr.text = re.sub(
                    r'STYLEREF\s+(?:\\"[^"]+\\"|"[^"]+"|[^\s\\]+)',
                    f'STYLEREF "{target_style}"',
                    text,
                    flags=re.I,
                )
        update_styleref_cached_text(xml_root, target_style, chapter_cache_text)
        even_text = header.get("evenPageText")
        if even_text:
            for t in xml_root.findall(".//w:t", namespaces=NS):
                if t.text and ("硕士学位论文" in t.text or "东南大学硕士学位论文" in t.text):
                    t.text = even_text


def flatten_chapters(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for ch in chapters:
        result.append(ch)
        result.extend(flatten_chapters(ch.get("subsections") or []))
    return result


def render_markdown_references(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    next_id = 1
    for ch in flatten_chapters(chapters):
        content = ch.get("content") or ""

        def replace(match: re.Match[str]) -> str:
            nonlocal next_id
            inner = match.group(1).strip()
            if inner.isdigit():
                return f"[[REF:{inner}]]"
            desc = inner.replace("KEYWORD_PLACEHOLDER:", "").strip()
            if not desc:
                return match.group(0)
            if desc not in seen:
                seen[desc] = next_id
                refs.append({"id": next_id, "description": desc, "placeholder": match.group(0)})
                next_id += 1
            return f"[[REF:{seen[desc]}]]"

        ch["content"] = re.sub(r"\[\[REF:(.*?)\]\]", replace, content)
    return refs


def set_plain_paragraph_text(p: etree._Element, text: str, proto: etree._Element | None = None) -> None:
    sample = sample_run_from(proto or p)
    empty_para_except_ppr(p)
    p.append(clean_run(sample, cleanup_spacing(text)))


def default_abstract_text(thesis: dict[str, Any], english: bool = False) -> str:
    title = thesis.get("title") or "the thesis topic"
    if english:
        return (
            f"This thesis studies {title}. It reviews related work, builds a deep learning baseline, "
            "introduces an attention-enhanced module for key-region feature selection, and evaluates "
            "the method through comparative experiments, ablation analysis, visualization, formulas, "
            "figures, tables, and references. Keywords: deep learning; tumor segmentation; attention "
            "mechanism; medical image; U-Net."
        )
    return (
        f"本文围绕《{title}》展开研究，梳理相关理论与研究现状，构建深度学习分割模型，"
        "并引入注意力增强模块以提升模型对关键区域和边界细节的表达能力。论文通过指标对比、"
        "消融实验和可视化分析验证方法有效性，同步给出公式、图、表、参考文献和正文引用。"
        "关键词：深度学习；肿瘤分割；注意力机制；医学图像；U-Net。"
    )


def cleanup_front_matter(
    body: etree._Element,
    protos: Prototypes,
    heading_styles: dict[int, str],
    thesis: dict[str, Any],
) -> None:
    def is_stop(node: etree._Element) -> bool:
        if is_section_break_node(node):
            return True
        local = etree.QName(node).localname
        if local != "p":
            return False
        text = para_text(node)
        sid = extract_style_id(node)
        if is_front_matter_title(text) or is_back_matter_title(text):
            return True
        return sid == heading_styles.get(1) and not is_front_matter_title(text) and not is_back_matter_title(text)

    for title_node in reversed([n for n in list(body) if etree.QName(n).localname == "p" and is_front_matter_title(para_text(n))]):
        title_text = normalize_for_match(para_text(title_node)).lower()
        if title_text not in {"摘要", "abstract"}:
            continue
        start = body.index(title_node) + 1
        end = start
        while end < len(body) and not is_stop(body[end]):
            end += 1
        content_nodes = list(body)[start:end]
        for node in content_nodes:
            body.remove(node)

        abstract = (
            thesis.get("abstractEn")
            or thesis.get("englishAbstract")
            or default_abstract_text(thesis, english=True)
            if title_text == "abstract"
            else thesis.get("abstractZh")
            or thesis.get("abstract")
            or default_abstract_text(thesis, english=False)
        )
        proto = first_present(protos.normal, title_node)
        p = clone_para_with_text(proto, abstract)
        body.insert(body.index(title_node) + 1, p)


def replace_body_content_with_chapters(
    root: etree._Element,
    thesis: dict[str, Any],
    references: list[dict[str, Any]] | None = None,
    style_settings: dict[str, Any] | None = None,
) -> None:
    styles_root = get_styles_root(root)
    body = get_body(root)
    heading_styles = build_heading_styles(styles_root)
    h1_style_name = style_name_by_id(styles_root, heading_styles.get(1, "Heading1"))
    chapters_for_headers = thesis.get("chapters") or []
    update_headers_and_footers(
        root,
        h1_style_name,
        style_settings,
        chapter_cache_text=chapter_header_cache_text(chapters_for_headers),
    )
    protos = find_prototypes(body, heading_styles)
    if protos.normal is None and protos.h1 is None:
        raise ValueError("Could not find any paragraph prototype in Word body")
    cleanup_front_matter(body, protos, heading_styles, thesis)

    children = list(body)
    start = -1
    end = -1
    for i, node in enumerate(children):
        if etree.QName(node).localname == "p":
            sid = extract_style_id(node)
            text = para_text(node)
            if sid == heading_styles.get(1) and not is_front_matter_title(text) and not is_back_matter_title(text):
                start = i
                break
    if start == -1:
        sect_pr = get_child(body, W_NS, "sectPr")
        anchor = sect_pr
    else:
        for i in range(start, len(children)):
            node = children[i]
            if etree.QName(node).localname == "p" and is_back_matter_title(para_text(node)):
                end = i
                break
            if is_section_break_node(node):
                end = i
                break
        if end == -1:
            end = len(children)
        for node in children[start:end]:
            body.remove(node)
        anchor = children[end] if end < len(children) and children[end].getparent() is body else get_child(body, W_NS, "sectPr")

    chapters = thesis.get("chapters") or []
    l1_for_refs = [ch for ch in chapters if int(ch.get("level") or 1) == 1] or chapters
    for idx, chapter in enumerate(l1_for_refs, start=1):
        render_visual_references_for_chapter(chapter, idx)
    generated_refs = render_markdown_references(chapters)
    references = list(references or thesis.get("references") or [])
    existing_ids = {int(ref.get("id") or 0) for ref in references}
    for ref in generated_refs:
        if int(ref.get("id") or 0) not in existing_ids:
            references.append(ref)
            existing_ids.add(int(ref.get("id") or 0))

    l1_index = 0
    counters = {"fig": 0, "tbl": 0, "eq": 0}

    def insert_before_anchor(node: etree._Element) -> None:
        if anchor is not None and anchor.getparent() is body:
            body.insert(body.index(anchor), node)
        else:
            body.append(node)

    def insert_chapter(chapter: dict[str, Any]) -> None:
        nonlocal l1_index, counters
        level = int(chapter.get("level") or 1)
        title = chapter.get("title") or "未命名章节"
        if level == 1:
            l1_index += 1
            counters = {"fig": 0, "tbl": 0, "eq": 0}
            proto = first_present(protos.h1, protos.normal)
            text = title if (style_settings or {}).get("keepHeadingNumbers") else strip_heading_numbering(title)
        elif level == 2:
            proto = first_present(protos.h2, protos.normal, protos.h1)
            text = title if (style_settings or {}).get("keepHeadingNumbers") else strip_heading_numbering(title)
        elif level == 3:
            proto = first_present(protos.h3, protos.normal, protos.h1)
            text = title if (style_settings or {}).get("keepHeadingNumbers") else strip_heading_numbering(title)
        else:
            proto = first_present(protos.normal, protos.h1)
            text = title
        if proto is not None:
            p_title = clone_para_with_text(proto, text)
            style_key = {1: "heading1", 2: "heading2", 3: "heading3"}.get(level)
            if style_key:
                apply_style_overrides(p_title, (style_settings or {}).get(style_key))
            insert_before_anchor(p_title)
        for node in create_content_nodes(chapter.get("content") or "", protos, max(l1_index, 1), counters, style_settings):
            insert_before_anchor(node)
        for child in chapter.get("subsections") or []:
            insert_chapter(child)

    for chapter in chapters:
        insert_chapter(chapter)

    write_references(body, protos, references, style_settings)
    ensure_update_fields(root)


def write_references(
    body: etree._Element,
    protos: Prototypes,
    references: list[dict[str, Any]],
    style_settings: dict[str, Any] | None = None,
) -> None:
    if not references or protos.ref_entry is None:
        return
    ref_header = None
    for node in body:
        if etree.QName(node).localname == "p" and is_back_matter_title(para_text(node)) and "参考文献" in normalize_for_match(para_text(node)):
            ref_header = node
            break
    if ref_header is None:
        ref_header = clone_para_with_text(first_present(protos.h1, protos.normal, protos.ref_entry), "参考文献")
        body.append(ref_header)

    idx = body.index(ref_header) + 1
    nodes_to_remove: list[etree._Element] = []
    while idx < len(body):
        node = body[idx]
        if is_section_break_node(node):
            break
        if etree.QName(node).localname != "p":
            break
        text = para_text(node).strip()
        if is_back_matter_title(text) and "参考文献" not in normalize_for_match(text):
            break
        nodes_to_remove.append(node)
        idx += 1
    for node in nodes_to_remove:
        body.remove(node)

    insert_at = body.index(ref_header) + 1
    sample = sample_run_from(protos.ref_entry)
    for ref in references:
        ref_id = int(ref.get("id") or len(references))
        desc = strip_ref_prefix(ref.get("description") or "")
        bm_id = next_global_id()
        bm_name = reference_bookmark_name(ref_id)
        p_ref = empty_para_except_ppr(deepcopy(protos.ref_entry))
        if has_paragraph_numbering(p_ref):
            p_ref.append(create_bookmark(bm_name, bm_id, True))
            p_ref.append(clean_run(sample, desc))
            p_ref.append(create_bookmark(bm_name, bm_id, False))
        else:
            remove_paragraph_numbering(p_ref)
            p_ref.append(create_bookmark(bm_name, bm_id, True))
            p_ref.append(clean_run(sample, f"[{ref_id}]"))
            p_ref.append(create_bookmark(bm_name, bm_id, False))
            p_ref.append(clean_run(sample, " " + desc))
        apply_style_overrides(p_ref, (style_settings or {}).get("reference"))
        body.insert(insert_at, p_ref)
        insert_at += 1


def ensure_update_fields(root: etree._Element) -> None:
    settings_root = get_part_xml_root(get_pkg_part(root, "/word/settings.xml"))
    if settings_root is None:
        return
    update = get_child(settings_root, W_NS, "updateFields")
    if update is None:
        update = etree.SubElement(settings_root, qn(W_NS, "updateFields"))
    update.set(qn(W_NS, "val"), "true")
    for fld_char in root.findall(".//w:fldChar", namespaces=NS):
        if get_attr(fld_char, W_NS, "fldCharType") == "begin":
            fld_char.set(qn(W_NS, "dirty"), "true")


def load_state(project_dir: str | Path) -> dict[str, Any]:
    state_path = Path(project_dir) / "09_state" / "project_state.json"
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    parsed_path = Path(project_dir) / "09_state" / "parsed_structure.json"
    parsed = json.loads(parsed_path.read_text(encoding="utf-8")) if parsed_path.exists() else {}
    return {
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "step": "writing",
        "thesis": {
            "title": parsed.get("title") or "未命名硕士论文",
            "chapters": parsed.get("chapters") or default_outline(),
        },
        "references": [],
        "styleSettings": {},
    }


def default_outline() -> list[dict[str, Any]]:
    return [
        {"id": "ch_1", "title": "第1章 绪论", "level": 1, "content": "", "subsections": []},
        {"id": "ch_2", "title": "第2章 相关理论与研究现状", "level": 1, "content": "", "subsections": []},
        {"id": "ch_3", "title": "第3章 研究方法与系统设计", "level": 1, "content": "", "subsections": []},
        {"id": "ch_4", "title": "第4章 实验设计与结果分析", "level": 1, "content": "", "subsections": []},
        {"id": "ch_5", "title": "第5章 总结与展望", "level": 1, "content": "", "subsections": []},
    ]


def write_state(project_dir: str | Path, state: dict[str, Any]) -> None:
    state["timestamp"] = datetime.now().isoformat()
    path = Path(project_dir) / "09_state" / "project_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_state_to_xml(
    project_dir: str | Path,
    template_xml: str | Path,
    output_xml: str | Path,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    project = Path(project_dir)
    state = state or load_state(project)
    tree = read_xml_tree(template_xml)
    root = require_flat_opc_root(tree)
    replace_body_content_with_chapters(
        root,
        state.get("thesis") or {},
        references=state.get("references") or [],
        style_settings=state.get("styleSettings") or {},
    )
    out_path = Path(output_xml)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_xml_tree(tree, out_path)
    return state
