#!/usr/bin/env python3
"""Crop a measured region and vectorize with vtracer (Layer A helper).

Usage:
  .venv/bin/python scripts/vectorize_region.py \\
      --image work/deck/original.png --box 896,156,75,63 \\
      --out-dir work/deck/assets --name icon1

Writes:
  <out-dir>/<name>.png   — crop
  <out-dir>/<name>.svg   — vtracer SVG
  <out-dir>/<name>_meta.json
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

try:
    import vtracer
except ImportError:
    vtracer = None


def vectorize(
    image: Path,
    box: tuple[int, int, int, int],
    out_dir: Path,
    name: str,
    *,
    colormode: str = "color",
    mode: str = "spline",
    filter_speckle: int = 4,
    color_precision: int = 6,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(image).convert("RGBA")
    x, y, w, h = box
    crop = im.crop((x, y, x + w, y + h))
    png_path = out_dir / f"{name}.png"
    svg_path = out_dir / f"{name}.svg"
    crop.save(png_path)

    svg_ok = False
    svg_err = None
    if vtracer is None:
        svg_err = "vtracer not installed"
    else:
        try:
            vtracer.convert_image_to_svg_py(
                str(png_path),
                str(svg_path),
                colormode=colormode,
                hierarchical="stacked",
                mode=mode,
                filter_speckle=filter_speckle,
                color_precision=color_precision,
                layer_difference=16,
                corner_threshold=60,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=8,
            )
            svg_ok = svg_path.exists() and svg_path.stat().st_size > 0
        except Exception as e:
            svg_err = str(e)

    meta = {
        "name": name,
        "source": str(image),
        "box_px": list(box),
        "png": str(png_path),
        "svg": str(svg_path) if svg_ok else None,
        "svg_bytes": svg_path.stat().st_size if svg_ok else 0,
        "svg_error": svg_err,
        "policy": "vectorize" if svg_ok else "picture",
        "layer": "A",
        "note": None
        if svg_ok
        else "PNG crop only — vtracer unavailable/failed (use picture policy)",
    }
    meta_path = out_dir / f"{name}_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", required=True)
    ap.add_argument("--box", required=True, help="x,y,w,h")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--colormode", default="color", choices=["color", "binary"])
    ap.add_argument("--mode", default="spline", choices=["spline", "polygon", "none"])
    ap.add_argument("--filter-speckle", type=int, default=4)
    args = ap.parse_args()
    box = tuple(int(v) for v in args.box.split(","))
    if len(box) != 4:
        ap.error("box must be x,y,w,h")
    meta = vectorize(
        Path(args.image),
        box,
        Path(args.out_dir),
        args.name,
        colormode=args.colormode,
        mode=args.mode,
        filter_speckle=args.filter_speckle,
    )
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
