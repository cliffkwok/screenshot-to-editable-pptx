#!/usr/bin/env python3
"""Convert pixel boxes into container-relative percentages and PPT inches.

Usage:
  python3 proportion_chain.py \
    --container-box "64,169,472,187" \
    --container-inch "13.33,7.5" \
    --elements "icon:120,200,80,80 badge:150,120,60,30 title:100,50,300,40" \
    --font-pct "title:8.2 body:3.1 caption:2.0" \
    --out proportions.json
"""
import argparse
import json
import re
import sys
from pathlib import Path


def parse_box(s: str):
    parts = [float(p.strip()) for p in s.split(",")]
    if len(parts) != 4:
        raise ValueError(f"Box must have 4 values x,y,w,h — got: {s}")
    return parts


def parse_wh(s: str):
    parts = [float(p.strip()) for p in s.split(",")]
    if len(parts) != 2:
        raise ValueError(f"Need w,h — got: {s}")
    return parts


def parse_elements(s: str):
    elements = []
    for item in s.split():
        m = re.match(r"([\w-]+):([\d.]+),([\d.]+),([\d.]+),([\d.]+)", item)
        if m:
            elements.append({
                "name": m.group(1),
                "box_px": [float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5))],
            })
    return elements


def compute_proportions(container_px, container_inch, slide_inch, elements):
    cx, cy, cw, ch = container_px
    cwi, chi = container_inch
    sw, sh = slide_inch
    ox = (sw - cwi) / 2 if cwi <= sw else 0
    oy = (sh - chi) / 2 if chi <= sh else 0

    results = {
        "container": {
            "box_px": container_px,
            "width_inch": cwi,
            "height_inch": chi,
            "origin_inch": [round(ox, 4), round(oy, 4)],
        },
        "slide_inch": [sw, sh],
        "elements": [],
    }

    for el in elements:
        ex, ey, ew, eh = el["box_px"]
        x_pct = (ex - cx) / cw * 100
        y_pct = (ey - cy) / ch * 100
        w_pct = ew / cw * 100
        h_pct = eh / ch * 100
        ppt_x = ox + cwi * x_pct / 100
        ppt_y = oy + chi * y_pct / 100
        ppt_w = cwi * w_pct / 100
        ppt_h = chi * h_pct / 100
        font_pt = (ppt_h * 0.65) * 72
        results["elements"].append({
            "name": el["name"],
            "box_px": el["box_px"],
            "proportion": {
                "x_pct": round(x_pct, 2),
                "y_pct": round(y_pct, 2),
                "w_pct": round(w_pct, 2),
                "h_pct": round(h_pct, 2),
            },
            "ppt": {
                "x_inch": round(ppt_x, 4),
                "y_inch": round(ppt_y, 4),
                "w_inch": round(ppt_w, 4),
                "h_inch": round(ppt_h, 4),
            },
            "font_estimate_pt": round(font_pt, 1),
            "slide_pct": {
                "x_pct": round(ppt_x / sw * 100, 2),
                "y_pct": round(ppt_y / sh * 100, 2),
                "w_pct": round(ppt_w / sw * 100, 2),
                "h_pct": round(ppt_h / sh * 100, 2),
            },
        })
    return results


def compute_font_chain(container_h_inch, font_heights_pct):
    chain = {}
    for label, pct in font_heights_pct.items():
        h_in = container_h_inch * pct / 100
        chain[label] = {
            "height_inch": round(h_in, 4),
            "pt": round(h_in * 72, 1),
        }
    return chain


def main():
    parser = argparse.ArgumentParser(description="px boxes → container % → PPT inches")
    parser.add_argument("--container-box", required=True, help="x,y,w,h in source pixels")
    parser.add_argument("--container-inch", required=True, help="target container w,h in inches")
    parser.add_argument("--slide-inch", default="13.33,7.5")
    parser.add_argument("--elements", required=True, help="'name:x,y,w,h name2:...'")
    parser.add_argument("--font-pct", default="", help="'title:8.2 body:3.1'")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    container_px = parse_box(args.container_box)
    container_inch = parse_wh(args.container_inch)
    slide_inch = parse_wh(args.slide_inch)
    elements = parse_elements(args.elements)
    if not elements:
        print("ERROR: no elements parsed from --elements")
        sys.exit(1)

    results = compute_proportions(container_px, container_inch, slide_inch, elements)
    if args.font_pct:
        font_pct = {}
        for item in args.font_pct.split():
            m = re.match(r"([\w-]+):([\d.]+)", item)
            if m:
                font_pct[m.group(1)] = float(m.group(2))
        results["font_chain"] = compute_font_chain(container_inch[1], font_pct)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved proportion data for {len(elements)} elements to {out_path}")


if __name__ == "__main__":
    main()
