#!/usr/bin/env python3
"""Eyedropper — exact single-pixel color like macOS Colors panel.

Prints RGB + Hex for one or more (x,y) samples. Use this instead of guessing
or averaging AA fringe.

Usage:
  python3 scripts/eyedropper.py --image shot.png --xy 710,82 --xy 640,160
  python3 scripts/eyedropper.py --image shot.png --xy 710,82 --label agent_stroke
  python3 scripts/eyedropper.py --image shot.png --xy 710,82 --out work/colors.json

Rules (02-color.md):
  - Fill  → interior pixel (inset ≥4px; avoid text/AA)
  - Stroke → mid-border pixel (not fringe toward fill or bg)
  - Ink   → darkest glyph pixel
  - If user posts Colors panel Hex → that value wins (source: panel)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required")
    sys.exit(1)


def hex_of(rgb):
    r, g, b = rgb[:3]
    return f"#{r:02X}{g:02X}{b:02X}"


def sample(im, x, y):
    px = im.load()
    w, h = im.size
    if not (0 <= x < w and 0 <= y < h):
        raise SystemExit(f"pixel ({x},{y}) out of bounds {w}×{h}")
    rgb = px[x, y]
    return {"x": x, "y": y, "rgb": list(rgb[:3]), "hex": hex_of(rgb)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", required=True)
    ap.add_argument("--xy", action="append", default=[], help="x,y (repeatable)")
    ap.add_argument("--label", action="append", default=[], help="label per --xy")
    ap.add_argument("--out", default="", help="optional JSON path")
    args = ap.parse_args()
    if not args.xy:
        ap.error("pass at least one --xy x,y")

    im = Image.open(args.image).convert("RGB")
    rows = []
    for i, raw in enumerate(args.xy):
        x, y = (int(v) for v in raw.replace(" ", "").split(","))
        label = args.label[i] if i < len(args.label) else f"sample_{i+1}"
        hit = sample(im, x, y)
        hit["label"] = label
        rows.append(hit)
        r, g, b = hit["rgb"]
        # macOS Colors panel style readout
        print(f"{label}")
        print(f"  pixel     ({x}, {y})")
        print(f"  Red       {r}")
        print(f"  Green     {g}")
        print(f"  Blue      {b}")
        print(f"  Hex Color # {hit['hex'].lstrip('#')}")
        print()

    if args.out:
        Path(args.out).write_text(json.dumps({"image": args.image, "samples": rows}, indent=2))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
