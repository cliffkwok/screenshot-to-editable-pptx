#!/usr/bin/env python3
"""Measure text ink on a screenshot: box, glyph height, pt, weight (bold?).

Uses stroke stem width vs glyph height. Calibrated on Arial:
  regular stem_em ≈ 0.10–0.15, bold ≈ 0.20+.

Usage:
  python3 text_measure.py --image shot.png --spec work/spec.json \\
      --out work/text_measure.json
  # or pass explicit boxes:
  python3 text_measure.py --image shot.png --boxes title:263,54,495,42 \\
      --slide-h 7.5 --out work/text_measure.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mapping import font_pt_from_glyph, refine_ink_box  # noqa: E402


def _border_median(px, x0, y0, x1, y1):
    samples = []
    for x in range(x0, x1):
        samples.append(px[x, y0][:3])
        samples.append(px[x, y1 - 1][:3])
    for y in range(y0, y1):
        samples.append(px[x0, y][:3])
        samples.append(px[x1 - 1, y][:3])
    if not samples:
        return (255, 255, 255)
    return (
        statistics.median(s[0] for s in samples),
        statistics.median(s[1] for s in samples),
        statistics.median(s[2] for s in samples),
    )


def stroke_stem_em(im: Image.Image, box, contrast=38) -> dict:
    """Median thin horizontal ink-run / glyph height ≈ stroke weight."""
    w, h = im.size
    x, y, bw, bh = [int(v) for v in box]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(w, x + bw), min(h, y + bh)
    if x1 - x0 < 3 or y1 - y0 < 4:
        return {"stem_em": 0.0, "stem_px": 0.0, "density": 0.0}
    rgb = im.convert("RGB")
    px = rgb.load()
    br, bg, bb = _border_median(px, x0, y0, x1, y1)
    ink = []
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            r, g, b = px[xx, yy]
            if max(abs(r - br), abs(g - bg), abs(b - bb)) >= contrast:
                ink.append((xx, yy))
    if len(ink) < 8:
        return {"stem_em": 0.0, "stem_px": 0.0, "density": 0.0}
    iy0 = min(p[1] for p in ink)
    iy1 = max(p[1] for p in ink)
    gh = max(1, iy1 - iy0 + 1)
    runs = []
    mid = (iy0 + iy1) // 2
    for yy in range(max(iy0, mid - 2), min(iy1 + 1, mid + 3)):
        run = 0
        for xx in range(x0, x1):
            r, g, b = px[xx, yy]
            if max(abs(r - br), abs(g - bg), abs(b - bb)) >= contrast:
                run += 1
            else:
                if 1 <= run <= max(2, int(gh * 0.42)):
                    runs.append(run)
                run = 0
        if 1 <= run <= max(2, int(gh * 0.42)):
            runs.append(run)
    stem = float(statistics.median(runs)) if runs else 0.0
    dens = len(ink) / max(1, (x1 - x0) * (y1 - y0))
    return {"stem_em": stem / gh, "stem_px": stem, "density": dens, "glyph_h_ink": gh}


def guess_bold(stem_em: float, glyph_h: int, density: float = 0.0, on_color: bool = False) -> bool:
    """Conservative: screenshot AA and white-on-color inflate stems.

    Default is regular. Only mark bold when the stroke is clearly thick
    on a large glyph and not sitting on a saturated header fill.
    """
    if on_color:
        return False  # white-on-brand bars look heavier than they are
    if glyph_h < 20:
        return False  # small type: stem runs are too noisy
    if density > 0.55:
        return False  # filled/blurred ink, not a reliable stem
    return stem_em >= 0.22


def bg_is_saturated(im: Image.Image, box) -> bool:
    """True when the text sits on a colorful header (not white/gray paper)."""
    w, h = im.size
    x, y, bw, bh = [int(v) for v in box]
    x0, y0 = max(0, x - 2), max(0, y - 2)
    x1, y1 = min(w, x + bw + 2), min(h, y + bh + 2)
    px = im.convert("RGB").load()
    chromas = []
    for yy in (y0, y1 - 1):
        for xx in range(x0, x1, max(1, (x1 - x0) // 12)):
            r, g, b = px[xx, yy]
            chromas.append(max(r, g, b) - min(r, g, b))
    for xx in (x0, x1 - 1):
        for yy in range(y0, y1, max(1, (y1 - y0) // 8)):
            r, g, b = px[xx, yy]
            chromas.append(max(r, g, b) - min(r, g, b))
    if not chromas:
        return False
    return statistics.median(chromas) >= 40


def looks_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in (text or ""))


def measure_box(im: Image.Image, box, slide_h=7.5, text="", name=""):
    img_w, img_h = im.size
    refined = refine_ink_box(im, box, extra_pad=2)
    if refined is None:
        ink_box, gh = [int(v) for v in box], int(box[3])
    else:
        ink_box, gh, _ = refined
        ink_box = list(ink_box)
    stroke = stroke_stem_em(im, ink_box)
    # Prefer thin-stem glyph height when refine swallowed padding / descenders.
    gh_use = stroke.get("glyph_h_ink") or gh
    if gh_use and gh and gh_use < gh * 0.92:
        gh = int(gh_use)
    script = "cjk" if looks_cjk(text) else "latin"
    on_color = bg_is_saturated(im, ink_box)
    bold = guess_bold(stroke["stem_em"], gh, stroke["density"], on_color=on_color)
    pt = font_pt_from_glyph(gh, img_h, slide_h, script)
    cx = ink_box[0] + ink_box[2] / 2.0
    cy = ink_box[1] + ink_box[3] / 2.0
    return {
        "name": name,
        "text": text,
        "box_px": ink_box,
        "glyph_height_px": gh,
        "cx_px": round(cx, 1),
        "cy_px": round(cy, 1),
        "font_pt": pt,
        "script": script,
        "bold": bold,
        "stem_em": round(stroke["stem_em"], 3),
        "density": round(stroke["density"], 3),
        "on_color_bg": on_color,
        "font_size_source": "measured",
        "bold_source": "measured",
    }


def boxes_from_spec(spec: dict) -> list[tuple[str, list, str]]:
    out = []
    for el in spec.get("elements") or []:
        if el.get("kind") not in ("text", "textbox") and not el.get("text"):
            continue
        if not el.get("box_px"):
            continue
        out.append((el.get("name", "?"), list(el["box_px"]), el.get("text") or ""))
    return out


def main():
    p = argparse.ArgumentParser(description="Measure screenshot text weight/size/position")
    p.add_argument("--image", required=True)
    p.add_argument("--spec", default="")
    p.add_argument("--boxes", default="", help="name:x,y,w,h name2:...")
    p.add_argument("--slide-h", type=float, default=7.5)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    image = Path(args.image)
    if not image.exists():
        print(f"ERROR: image not found: {image}")
        sys.exit(1)
    im = Image.open(image).convert("RGB")

    items = []
    if args.spec:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        items.extend(boxes_from_spec(spec))
    if args.boxes:
        for tok in args.boxes.split():
            name, rest = tok.split(":", 1)
            x, y, w, h = [int(v) for v in rest.split(",")]
            items.append((name, [x, y, w, h], ""))

    if not items:
        print("ERROR: pass --spec with box_px elements or --boxes")
        sys.exit(1)

    lines = [measure_box(im, box, args.slide_h, text=text, name=name) for name, box, text in items]
    out = {
        "image": str(image),
        "width_px": im.size[0],
        "height_px": im.size[1],
        "slide_h_in": args.slide_h,
        "lines": lines,
        "by_name": {L["name"]: L for L in lines},
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"text_measure: {len(lines)} lines → {args.out}")
    for L in lines:
        wt = "BOLD" if L["bold"] else "reg "
        print(
            f"  {L['name']:14} {wt} {L['font_pt']:5}pt  "
            f"stem_em={L['stem_em']:.3f}  on_color={L.get('on_color_bg')}  "
            f"box={L['box_px']}  c=({L['cx_px']},{L['cy_px']})  {L.get('text','')[:40]!r}"
        )


if __name__ == "__main__":
    main()
