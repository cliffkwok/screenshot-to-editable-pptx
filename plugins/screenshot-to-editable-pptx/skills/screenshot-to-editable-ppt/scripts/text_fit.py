#!/usr/bin/env python3
"""Compare original vs PowerPoint render ink for each spec text line.

Writes dx/dy (original px) and a corrected font_pt so a rebuild can nudge
boxes that drifted and sizes that came out larger/smaller than the photo.

Usage:
  python3 text_fit.py --original shot.png --render work/render.png \\
      --spec work/spec.json --out work/text_fit.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mapping import pct_to_px, refine_ink_box  # noqa: E402


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    im = im.convert("RGB")
    w, h = im.size
    scale = max(tw / w, th / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - tw) // 2)
    top = max(0, (nh - th) // 2)
    return resized.crop((left, top, left + tw, top + th))


def orig_to_fitted(box, orig_w, orig_h, tw, th):
    x, y, w, h = [float(v) for v in box]
    scale = max(tw / orig_w, th / orig_h)
    nw, nh = orig_w * scale, orig_h * scale
    left, top = (nw - tw) / 2.0, (nh - th) / 2.0
    return [x * scale - left, y * scale - top, w * scale, h * scale], scale


def ink_stats(im, box, pad=8):
    x, y, w, h = [int(round(v)) for v in box]
    search = [x - pad, y - pad, w + 2 * pad, h + 2 * pad]
    refined = refine_ink_box(im, search, extra_pad=0)
    if refined is None:
        return None
    bx, gh, count = refined
    cx = bx[0] + bx[2] / 2.0
    cy = bx[1] + bx[3] / 2.0
    return {"box": bx, "glyph_h": gh, "cx": cx, "cy": cy, "count": count}


def main():
    p = argparse.ArgumentParser(description="Nudge spec text from original vs render ink")
    p.add_argument("--original", required=True)
    p.add_argument("--render", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    orig = Image.open(args.original).convert("RGB")
    rend = Image.open(args.render).convert("RGB")
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    ow, oh = orig.size
    slide = spec.get("slide") or {}
    slide_w = float(slide.get("width_in", 13.33))
    slide_h = float(slide.get("height_in", 7.5))
    fit = (spec.get("source") or {}).get("fit") or "height"
    src_w = (spec.get("source") or {}).get("width_px") or ow
    src_h = (spec.get("source") or {}).get("height_px") or oh

    tw, th = 1600, 900
    of = fit_cover(orig, tw, th)
    rf = fit_cover(rend, tw, th)

    lines = {}
    for el in spec.get("elements") or []:
        if el.get("kind") not in ("text", "textbox") and not el.get("text"):
            continue
        if el.get("font_size_pt") is None:
            continue
        name = el["name"]
        if el.get("box_px"):
            box = list(el["box_px"])
        else:
            box = list(pct_to_px(
                el["x_pct"], el["y_pct"], el["w_pct"], el["h_pct"],
                src_w, src_h, slide_w, slide_h, fit,
            ))
        fbox, scale = orig_to_fitted(box, ow, oh, tw, th)
        o_ink = ink_stats(of, fbox)
        r_ink = ink_stats(rf, fbox)
        rec = {
            "box_px": [int(round(v)) for v in box],
            "font_pt_in": el["font_size_pt"],
        }
        if o_ink and r_ink and r_ink["glyph_h"] >= 4 and o_ink["glyph_h"] >= 4:
            box_h = max(1.0, fbox[3])
            dx = (o_ink["cx"] - r_ink["cx"]) / scale
            dy = (o_ink["cy"] - r_ink["cy"]) / scale
            dx = max(-10.0, min(10.0, dx))
            dy = max(-10.0, min(10.0, dy))
            # Frame/diagram ink: original glyph much taller than the spec box.
            if o_ink["glyph_h"] > box_h * 1.65 or r_ink["glyph_h"] > box_h * 1.65:
                rec.update({
                    "dx_px": 0, "dy_px": 0,
                    "font_pt": el["font_size_pt"], "skipped": True, "reason": "extra_ink",
                })
            elif o_ink["glyph_h"] >= box_h * 0.92:
                # Size locked; still allow a small centroid nudge.
                rec.update({
                    "dx_px": round(dx, 1) if abs(dx) <= 4 else 0,
                    "dy_px": round(dy, 1) if abs(dy) <= 4 else 0,
                    "font_pt": el["font_size_pt"], "skipped": True, "reason": "box_filled",
                })
            elif r_ink["glyph_h"] < o_ink["glyph_h"] * 0.45 or o_ink["glyph_h"] < r_ink["glyph_h"] * 0.45:
                rec.update({
                    "dx_px": 0, "dy_px": 0,
                    "font_pt": el["font_size_pt"], "skipped": True, "reason": "glyph_mismatch",
                })
            else:
                pt_scale = o_ink["glyph_h"] / r_ink["glyph_h"]
                pt_scale = max(0.88, min(1.10, pt_scale))
                new_pt = round(el["font_size_pt"] * pt_scale, 1)
                rec.update({
                    "dx_px": round(dx, 1),
                    "dy_px": round(dy, 1),
                    "font_pt": new_pt,
                    "orig_glyph_h": o_ink["glyph_h"],
                    "render_glyph_h": r_ink["glyph_h"],
                    "pt_scale": round(pt_scale, 3),
                })
        else:
            rec.update({"dx_px": 0, "dy_px": 0, "font_pt": el["font_size_pt"], "skipped": True})
        # Always carry measured bold if present on the element
        if "bold" in el:
            rec["bold"] = bool(el["bold"])
        lines[name] = rec

    out = {"lines": lines, "original": str(args.original), "render": str(args.render)}
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"text_fit: {len(lines)} lines → {args.out}")
    for name, rec in lines.items():
        if rec.get("skipped"):
            print(f"  {name}: skipped")
            continue
        print(
            f"  {name}: dx={rec['dx_px']:+.1f} dy={rec['dy_px']:+.1f}  "
            f"{rec['font_pt_in']}pt → {rec['font_pt']}pt  "
            f"(glyph {rec['orig_glyph_h']} vs {rec['render_glyph_h']})"
        )


if __name__ == "__main__":
    main()
