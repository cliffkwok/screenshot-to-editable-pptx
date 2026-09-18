#!/usr/bin/env python3
"""Detect progress/scrubber as grey track (back) + black fill (front)."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required"); sys.exit(1)

def is_black(rgb, thr=40):
    return rgb[0] <= thr and rgb[1] <= thr and rgb[2] <= thr

def is_grey(rgb, lo=160, hi=235):
    r, g, b = rgb
    return lo <= r <= hi and abs(r - g) <= 10 and abs(g - b) <= 10

def find_progress_y(im):
    w, h = im.size
    px = im.load()
    best_y, best_n = None, 0
    for y in range(int(h * 0.7), h - 4):
        n = sum(1 for x in range(w) if is_black(px[x, y]) or is_grey(px[x, y]))
        if n > best_n and n > w * 0.2:
            best_n, best_y = n, y
    return best_y

def runs_on_row(px, y, w, pred):
    out, x = [], 0
    while x < w:
        if pred(px[x, y]):
            x0 = x
            while x < w and pred(px[x, y]):
                x += 1
            if x - x0 >= 4:
                out.append((x0, x - 1))
        else:
            x += 1
    return out

def band_height(px, y0, x0, x1, pred, h, max_span=12):
    top = y0
    while top > 0:
        hit = sum(1 for x in range(x0, x1 + 1) if pred(px[x, top - 1]))
        if hit < (x1 - x0 + 1) * 0.5:
            break
        top -= 1
        if y0 - top > max_span:
            break
    bot = y0
    while bot + 1 < h:
        hit = sum(1 for x in range(x0, x1 + 1) if pred(px[x, bot + 1]))
        if hit < (x1 - x0 + 1) * 0.5:
            break
        bot += 1
        if bot - y0 > max_span:
            break
    return top, bot

def detect(im, y=None):
    w, h = im.size
    px = im.load()
    y = y if y is not None else find_progress_y(im)
    if y is None:
        return {"found": False, "reason": "no progress-like row"}
    black_runs = runs_on_row(px, y, w, is_black)
    grey_runs = runs_on_row(px, y, w, is_grey)
    if not black_runs and not grey_runs:
        return {"found": False, "reason": f"no black/grey at y={y}"}
    fills = []
    for x0, x1 in black_runs:
        t, b = band_height(px, y, x0, x1, is_black, h)
        fills.append({"box": [x0, t, x1 - x0 + 1, b - t + 1], "fill": "#000000"})
    tracks = []
    for i, (x0, x1) in enumerate(black_runs):
        right = x1
        if i == len(black_runs) - 1:
            for gx0, gx1 in grey_runs:
                if gx0 <= right + 6:
                    right = max(right, gx1)
        t, b = band_height(px, y, x0, right, lambda c: is_black(c) or is_grey(c), h)
        g = px[min(w - 1, right - 2), y]
        hex_g = f"#{g[0]:02X}{g[1]:02X}{g[2]:02X}" if is_grey(g) else "#DDDDDD"
        tracks.append({"box": [x0, t, right - x0 + 1, b - t + 1], "fill": hex_g})
    for gx0, gx1 in grey_runs:
        covered = any(not (gx1 < t["box"][0] or gx0 > t["box"][0] + t["box"][2] - 1) for t in tracks)
        if not covered:
            t, b = band_height(px, y, gx0, gx1, is_grey, h)
            g = px[(gx0 + gx1) // 2, y]
            tracks.append({"box": [gx0, t, gx1 - gx0 + 1, b - t + 1], "fill": f"#{g[0]:02X}{g[1]:02X}{g[2]:02X}"})
    return {
        "found": True,
        "y": y,
        "rule": "two overlapping layers: grey track (back) + black fill (front)",
        "tracks": tracks,
        "fills": fills,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--y", type=int, default=None)
    p.add_argument("--out", default=None)
    args = p.parse_args()
    result = detect(Image.open(args.image).convert("RGB"), args.y)
    text = json.dumps(result, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text)
    sys.exit(0 if result.get("found") else 1)

if __name__ == "__main__":
    main()
