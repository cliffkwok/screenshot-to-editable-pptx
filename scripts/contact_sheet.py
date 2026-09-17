#!/usr/bin/env python3
"""Build a contact sheet from Layer A asset PNGs (universal QA).

Usage:
  python3 scripts/contact_sheet.py \\
      --assets work/deck/assets --out work/deck/assets/_contact_sheet.png \\
      --cols 3 --pad 8 --label
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow required")
    sys.exit(1)


def gather_pngs(assets: Path, glob: str = "*.png") -> list[Path]:
    files = sorted(
        p
        for p in assets.glob(glob)
        if p.is_file() and not p.name.startswith("_") and "_contact" not in p.name
    )
    return files


def contact_sheet(
    paths: list[Path],
    *,
    cols: int = 3,
    pad: int = 10,
    bg: str = "#F0F0F0",
    cell: int | None = None,
    label: bool = True,
) -> Image.Image:
    if not paths:
        raise ValueError("no PNGs to sheet")
    imgs = [Image.open(p).convert("RGBA") for p in paths]
    # cell size = max side among thumbs (or fixed)
    if cell is None:
        cell = max(max(im.size) for im in imgs)
    cell = max(cell, 32)
    rows = (len(imgs) + cols - 1) // cols
    label_h = 18 if label else 0
    W = cols * cell + (cols + 1) * pad
    H = rows * (cell + label_h) + (rows + 1) * pad
    sheet = Image.new("RGB", (W, H), bg)
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    for i, (path, im) in enumerate(zip(paths, imgs)):
        r, c = divmod(i, cols)
        # fit in cell
        scale = min(cell / im.width, cell / im.height, 1.0)
        tw, th = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        thumb = im.resize((tw, th), Image.Resampling.LANCZOS)
        x0 = pad + c * (cell + pad)
        y0 = pad + r * (cell + label_h + pad)
        # checker / white tile behind
        tile = Image.new("RGBA", (cell, cell), (255, 255, 255, 255))
        ox, oy = (cell - tw) // 2, (cell - th) // 2
        tile.paste(thumb, (ox, oy), thumb)
        sheet.paste(tile.convert("RGB"), (x0, y0))
        if label:
            dr.text((x0, y0 + cell + 2), path.stem[:24], fill=(40, 40, 40), font=font)
    return sheet


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--assets", required=True, help="folder of PNG crops")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--pad", type=int, default=10)
    ap.add_argument("--cell", type=int, default=0, help="cell size px (0=auto)")
    ap.add_argument("--label", action="store_true", default=True)
    ap.add_argument("--no-label", action="store_true")
    args = ap.parse_args()
    assets = Path(args.assets)
    paths = gather_pngs(assets)
    if not paths:
        print(f"ERROR: no PNGs in {assets}")
        sys.exit(1)
    sheet = contact_sheet(
        paths,
        cols=args.cols,
        pad=args.pad,
        cell=args.cell or None,
        label=not args.no_label,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"contact sheet {len(paths)} assets → {out} ({sheet.size[0]}×{sheet.size[1]})")


if __name__ == "__main__":
    main()
