#!/usr/bin/env python3
"""Detect stacked crosshair / slider selected markers in a screenshot.

A selected marker is NEVER one shape. It is a stack of three roles:

  1. horizontal track  — grey line (thicker)
  2. vertical stem     — grey line (thinner), usually rising from the track
  3. accent circle     — colored oval centered on the intersection

Usage:
  python3 scripts/detect_stacked_marker.py --image shot.png --out marker.json
  python3 scripts/detect_stacked_marker.py --image shot.png --roi 480,200,60,50

Build with helpers.add_crosshair_marker(...) using the JSON roles.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required", file=sys.stderr)
    sys.exit(1)


def _hex(rgb) -> str:
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


def _is_grey(r, g, b, lo=150, hi=235) -> bool:
    L = (r + g + b) / 3
    return lo < L < hi and abs(r - g) < 28 and abs(g - b) < 28 and abs(r - b) < 32


def _is_accent(r, g, b) -> bool:
    """Saturated non-grey (blue/green/red thumb)."""
    L = (r + g + b) / 3
    if L > 230 or L < 40:
        return False
    if _is_grey(r, g, b, lo=100, hi=240):
        return False
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) > 35 and mx > 100


def detect_stacked_marker(im: Image.Image, roi=None) -> dict | None:
    """Return marker roles or None if not found.

    roi: optional (x, y, w, h) search box. Prefer a box around the selected dot.
    """
    rgb = im.convert("RGB")
    W, H = rgb.size
    if roi:
        x0, y0, rw, rh = roi
        x1, y1 = x0 + rw, y0 + rh
    else:
        x0, y0, x1, y1 = 0, 0, W, H

    px = rgb.load()

    # 1) Accent pixels → densest local cluster (ignore distant blues)
    accents = []
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            r, g, b = px[x, y]
            if _is_accent(r, g, b):
                accents.append((x, y, r, g, b))
    if len(accents) < 8:
        return None

    best_c, best_n = None, 0
    xs = [t[0] for t in accents]
    ys = [t[1] for t in accents]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            n = sum(1 for a in accents if abs(a[0] - x) <= 8 and abs(a[1] - y) <= 8)
            if n > best_n:
                best_n, best_c = n, (x, y)
    if best_c is None or best_n < 8:
        return None
    accents = [
        t for t in accents
        if abs(t[0] - best_c[0]) <= 10 and abs(t[1] - best_c[1]) <= 10
    ]
    if len(accents) < 8:
        return None

    axs = [t[0] for t in accents]
    ays = [t[1] for t in accents]
    cx = (min(axs) + max(axs)) // 2
    cy = (min(ays) + max(ays)) // 2
    diam = max(max(axs) - min(axs), max(ays) - min(ays)) + 1
    accents.sort(key=lambda t: t[2] + t[3] + t[4])
    q = accents[: max(1, len(accents) // 4)]
    circle_rgb = (
        sum(t[2] for t in q) // len(q),
        sum(t[3] for t in q) // len(q),
        sum(t[4] for t in q) // len(q),
    )

    # 2) Horizontal track — grey runs on both sides of the circle
    def grey_run_at(yy):
        left, right, cols = [], [], []
        for x in range(cx - 1, max(0, x0) - 1, -1):
            r, g, b = px[x, yy]
            if _is_grey(r, g, b):
                left.append(x)
                cols.append((r, g, b))
            elif abs(x - cx) <= diam // 2 + 1:
                continue
            else:
                break
        for x in range(cx + 1, min(W, x1)):
            r, g, b = px[x, yy]
            if _is_grey(r, g, b):
                right.append(x)
                cols.append((r, g, b))
            elif abs(x - cx) <= diam // 2 + 1:
                continue
            else:
                break
        return left, right, cols

    track_cols = []
    track_x0 = track_x1 = cx
    chosen_y = cy
    for dy in (0, -1, 1, -2, 2, 3, -3):
        yy = cy + dy
        if not (0 <= yy < H):
            continue
        left, right, cols = grey_run_at(yy)
        if len(left) + len(right) >= max(6, diam):
            chosen_y = yy
            track_cols = cols
            track_x0 = min(left) if left else cx - diam
            track_x1 = max(right) if right else cx + diam
            break
    cy = chosen_y
    if not track_cols:
        return None

    tx = track_x0 if abs(track_x0 - cx) > diam // 2 else track_x1
    y_lo, y_hi = cy, cy
    while y_lo > 0 and _is_grey(*px[tx, y_lo - 1]):
        y_lo -= 1
    while y_hi < H - 1 and _is_grey(*px[tx, y_hi + 1]):
        y_hi += 1
    track_px = max(1, y_hi - y_lo + 1)
    track_rgb = (
        sum(c[0] for c in track_cols) // len(track_cols),
        sum(c[1] for c in track_cols) // len(track_cols),
        sum(c[2] for c in track_cols) // len(track_cols),
    )

    # 3) Vertical stem — grey column above circle (may be faint)
    stem_pts = []
    bg = px[max(0, cx - 12), max(0, min(ays) - 8)]
    bgL = sum(bg) / 3
    for y in range(max(0, y0), min(ays) + 1):
        for x in range(cx - 3, cx + 4):
            if not (0 <= x < W):
                continue
            r, g, b = px[x, y]
            L = (r + g + b) / 3
            if _is_grey(r, g, b, lo=130, hi=245) and L < bgL - 4:
                stem_pts.append((x, y, r, g, b))
            elif _is_grey(r, g, b, lo=160, hi=235):
                stem_pts.append((x, y, r, g, b))

    stem_rgb = track_rgb
    stem_top = min(ays) - max(4, diam // 2)
    stem_bot = cy
    stem_px = max(1, track_px - 1)
    if stem_pts:
        stem_top = min(t[1] for t in stem_pts)
        stem_bot = max(t[1] for t in stem_pts)
        my = (stem_top + min(ays)) // 2
        run = best = 0
        for x in range(cx - 6, cx + 7):
            if 0 <= x < W and 0 <= my < H and _is_grey(*px[x, my], lo=140, hi=245):
                run += 1
                best = max(best, run)
            else:
                run = 0
        stem_px = max(1, best or stem_px)
        sr = sum(t[2] for t in stem_pts) // len(stem_pts)
        sg = sum(t[3] for t in stem_pts) // len(stem_pts)
        sb = sum(t[4] for t in stem_pts) // len(stem_pts)
        stem_rgb = (sr, sg, sb)
        if _is_accent(*stem_rgb) or (
            stem_rgb[2] > stem_rgb[0] + 25 and stem_rgb[2] > stem_rgb[1] + 15
        ):
            stem_rgb = track_rgb

    if stem_bot < cy:
        stem_bot = cy

    return {
        "kind": "crosshair_marker",
        "roles": {
            "track": {
                "axis": "h",
                "color": _hex(track_rgb),
                "stroke_px": track_px,
                "y": cy,
                "x0": track_x0,
                "x1": track_x1,
                "note": "Shared track — usually one long line for the whole slider",
            },
            "stem": {
                "axis": "v",
                "color": _hex(stem_rgb),
                "stroke_px": stem_px,
                "x": cx,
                "y0": stem_top,
                "y1": stem_bot,
                "note": "Same grey family as track — NOT accent color",
            },
            "circle": {
                "color": _hex(circle_rgb),
                "cx": cx,
                "cy": cy,
                "diameter_px": diam,
                "bbox": [min(axs), min(ays), diam, diam],
            },
        },
        "z_order": ["track", "stem", "circle"],
        "group": ["stem", "circle"],
        "law": (
            "Stacked marker = grey H track + grey V stem + accent circle. "
            "Never one oval. Never paint the stem in the circle accent color."
        ),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image", required=True)
    p.add_argument("--roi", default="", help="x,y,w,h optional search box")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    im = Image.open(args.image)
    roi = None
    if args.roi.strip():
        roi = tuple(int(x) for x in args.roi.split(","))
        if len(roi) != 4:
            print("ERROR: --roi must be x,y,w,h", file=sys.stderr)
            sys.exit(2)
    result = detect_stacked_marker(im, roi=roi)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if result is None:
        out.write_text(json.dumps({"found": False}, indent=2))
        print("NO stacked marker found")
        sys.exit(1)
    payload = {"found": True, **result}
    out.write_text(json.dumps(payload, indent=2))
    roles = result["roles"]
    print(
        f"FOUND crosshair_marker  track={roles['track']['color']} "
        f"{roles['track']['stroke_px']}px  stem={roles['stem']['color']} "
        f"{roles['stem']['stroke_px']}px  circle={roles['circle']['color']} "
        f"d={roles['circle']['diameter_px']}px @ "
        f"({roles['circle']['cx']},{roles['circle']['cy']})"
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
