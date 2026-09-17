#!/usr/bin/env python3
"""Write / validate a Layer A/B/C inventory JSON for a deck.

Example inventory item:
  {"id": "icon1", "layer": "A", "box_px": [896,156,75,63],
   "policy": "picture", "asset": "assets/icon1.png", "note": "3D bed"}

Usage:
  python3 scripts/layer_inventory.py --write work/deck/_layers.json --from-json items.json
  python3 scripts/layer_inventory.py --check work/deck/_layers.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED = ("id", "layer", "box_px")
LAYERS = {"A", "B", "C"}
POLICIES_A = {"shape_group", "vectorize", "picture"}


def validate(items: list[dict]) -> list[str]:
    errs = []
    ids = set()
    for i, it in enumerate(items):
        for k in REQUIRED:
            if k not in it:
                errs.append(f"[{i}] missing {k}")
        layer = it.get("layer")
        if layer not in LAYERS:
            errs.append(f"[{i}] layer must be A|B|C, got {layer!r}")
        box = it.get("box_px")
        if not (isinstance(box, list) and len(box) == 4):
            errs.append(f"[{i}] box_px must be [x,y,w,h]")
        eid = it.get("id")
        if eid in ids:
            errs.append(f"[{i}] duplicate id {eid}")
        ids.add(eid)
        if layer == "A":
            pol = it.get("policy")
            if pol and pol not in POLICIES_A:
                errs.append(f"[{i}] A policy must be {POLICIES_A}")
        if layer == "C" and it.get("policy") == "picture":
            errs.append(f"[{i}] text must not be a picture (Layer C)")
    return errs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", help="validate inventory JSON")
    ap.add_argument("--write", help="path to write inventory")
    ap.add_argument("--from-json", help="items array JSON path")
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    if args.check:
        data = json.loads(Path(args.check).read_text())
        items = data.get("elements") or data
        errs = validate(items)
        if errs:
            print("FAIL")
            for e in errs:
                print(" ", e)
            sys.exit(1)
        print(f"OK  {len(items)} elements")
        for it in items:
            print(f"  [{it['layer']}] {it['id']}  box={it['box_px']}  {it.get('policy','')}")
        return

    if args.write and args.from_json:
        items = json.loads(Path(args.from_json).read_text())
        if isinstance(items, dict):
            items = items.get("elements") or []
        errs = validate(items)
        if errs:
            print("FAIL validation")
            for e in errs:
                print(" ", e)
            sys.exit(1)
        out = {
            "title": args.title,
            "elements": items,
            "counts": {
                "A": sum(1 for x in items if x["layer"] == "A"),
                "B": sum(1 for x in items if x["layer"] == "B"),
                "C": sum(1 for x in items if x["layer"] == "C"),
            },
        }
        Path(args.write).write_text(json.dumps(out, indent=2))
        print("wrote", args.write, out["counts"])
        return

    ap.error("use --check PATH or --write PATH --from-json PATH")


if __name__ == "__main__":
    main()
