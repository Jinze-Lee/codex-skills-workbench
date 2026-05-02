from __future__ import annotations

import argparse
import json
from pathlib import Path

from word_xml_core import parse_template_xml


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Parse Flat OPC Word XML into template structure JSON.")
    ap.add_argument("template_xml")
    ap.add_argument("out_json")
    args = ap.parse_args(argv)

    result = parse_template_xml(args.template_xml)
    out = Path(args.out_json).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

