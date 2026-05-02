from __future__ import annotations

from pathlib import Path
import base64
import zipfile
from lxml import etree

PKG_NS = "http://schemas.microsoft.com/office/2006/xmlPackage"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

NSMAP = {"pkg": PKG_NS}


def _load_content_types(zf: zipfile.ZipFile):
    ct_xml = zf.read("[Content_Types].xml")
    root = etree.fromstring(ct_xml)
    defaults = {}
    overrides = {}
    for child in root:
        local = etree.QName(child).localname
        if local == "Default":
            defaults[child.get("Extension")] = child.get("ContentType")
        elif local == "Override":
            overrides[child.get("PartName")] = child.get("ContentType")
    return defaults, overrides


def _guess_content_type(zip_name: str, defaults: dict[str, str], overrides: dict[str, str]) -> str:
    part_name = "/" + zip_name if not zip_name.startswith("/") else zip_name
    if part_name in overrides:
        return overrides[part_name]
    ext = zip_name.rsplit(".", 1)[-1] if "." in zip_name else ""
    return defaults.get(ext, "application/octet-stream")


def sniff_xml_kind(xml_path: str | Path) -> str:
    head = Path(xml_path).read_text(encoding="utf-8", errors="ignore")[:4000]
    if "<pkg:package" in head and "http://schemas.microsoft.com/office/2006/xmlPackage" in head:
        return "flat_opc"
    if "<w:wordDocument" in head and "http://schemas.microsoft.com/office/word/2003/wordml" in head:
        return "word_2003_xml"
    if "<office:document" in head and "urn:oasis:names:tc:opendocument:xmlns:office:1.0" in head:
        return "odf_flat_xml"
    return "unknown"


def docx_to_flat_opc_xml(docx_path: str | Path, xml_path: str | Path) -> None:
    docx_path = Path(docx_path).resolve()
    xml_path = Path(xml_path).resolve()

    with zipfile.ZipFile(docx_path, "r") as zf:
        defaults, overrides = _load_content_types(zf)

        root = etree.Element(f"{{{PKG_NS}}}package", nsmap={"pkg": PKG_NS})

        for zip_name in zf.namelist():
            if zip_name == "[Content_Types].xml":
                continue

            raw = zf.read(zip_name)
            content_type = _guess_content_type(zip_name, defaults, overrides)

            part = etree.SubElement(root, f"{{{PKG_NS}}}part")
            part.set(f"{{{PKG_NS}}}name", "/" + zip_name)
            part.set(f"{{{PKG_NS}}}contentType", content_type)

            is_xml_like = zip_name.endswith(".xml") or zip_name.endswith(".rels")
            if is_xml_like:
                xml_data = etree.SubElement(part, f"{{{PKG_NS}}}xmlData")
                try:
                    elem = etree.fromstring(raw)
                    xml_data.append(elem)
                except Exception:
                    part.remove(xml_data)
                    binary_data = etree.SubElement(part, f"{{{PKG_NS}}}binaryData")
                    binary_data.text = base64.encodebytes(raw).decode("ascii")
            else:
                binary_data = etree.SubElement(part, f"{{{PKG_NS}}}binaryData")
                binary_data.text = base64.encodebytes(raw).decode("ascii")

        body = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone="yes")
        prefix = b'<?mso-application progid="Word.Document"?>\n'
        xml_path.write_bytes(body[: body.find(b"?>") + 2] + b"\n" + prefix + body[body.find(b"?>") + 2 :])


def _build_content_types(entries: list[tuple[str, str]]) -> bytes:
    root = etree.Element(f"{{{CT_NS}}}Types", nsmap={None: CT_NS})
    etree.SubElement(
        root,
        f"{{{CT_NS}}}Default",
        Extension="rels",
        ContentType="application/vnd.openxmlformats-package.relationships+xml",
    )
    etree.SubElement(
        root,
        f"{{{CT_NS}}}Default",
        Extension="xml",
        ContentType="application/xml",
    )

    for part_name, content_type in entries:
        etree.SubElement(
            root,
            f"{{{CT_NS}}}Override",
            PartName=part_name,
            ContentType=content_type,
        )

    return etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone="yes")


def flat_opc_xml_to_docx(xml_path: str | Path, docx_path: str | Path) -> None:
    xml_path = Path(xml_path).resolve()
    docx_path = Path(docx_path).resolve()

    parser = etree.XMLParser(remove_blank_text=False, recover=True, huge_tree=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()

    parts = root.findall("pkg:part", namespaces=NSMAP)
    entries: list[tuple[str, str, str, bytes]] = []

    for part in parts:
        name = part.get(f"{{{PKG_NS}}}name")
        content_type = part.get(f"{{{PKG_NS}}}contentType") or "application/octet-stream"
        zip_name = name.lstrip("/")

        if len(part) == 0:
            payload = b""
        else:
            node = part[0]
            local = etree.QName(node).localname

            if local == "xmlData":
                if len(node):
                    payload = etree.tostring(
                        node[0],
                        encoding="UTF-8",
                        xml_declaration=True,
                        standalone="yes",
                    )
                else:
                    payload = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            elif local == "binaryData":
                payload = base64.b64decode("".join(node.itertext()))
            else:
                raise ValueError(f"Unknown pkg child node: {local}")

        entries.append((name, content_type, zip_name, payload))

    with zipfile.ZipFile(docx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _build_content_types([(n, ct) for n, ct, _, _ in entries]))
        for _, _, zip_name, payload in entries:
            zf.writestr(zip_name, payload)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage:")
        print('  python flat_opc_converter.py toxml  "input.docx" "output.xml"')
        print('  python flat_opc_converter.py todocx "input.xml"  "output.docx"')
        sys.exit(1)

    mode, src, dst = sys.argv[1].lower(), sys.argv[2], sys.argv[3]

    if mode == "toxml":
        docx_to_flat_opc_xml(src, dst)
        print(f"done -> {dst}")
        print(f"kind = {sniff_xml_kind(dst)}")
    elif mode == "todocx":
        flat_opc_xml_to_docx(src, dst)
        print(f"done -> {dst}")
    else:
        raise ValueError(f"Unknown mode: {mode}")
