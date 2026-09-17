#!/usr/bin/env python3
"""Compare an original slide screenshot to a PowerPoint-rendered PNG.

Fails when layout drifted the way python-pptx inspect cannot see:
cards stacked at the origin, highlight covering the wrong glyphs, missing
sibling shapes. Color/font still belong to verify_pptx.py.

Usage:
  python3 compare_render.py --original shot.png --render render.png --out work/compare
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required")
    sys.exit(1)


def is_cream(rgb, tol=28):
    r, g, b = rgb
    if r > 250 and g > 250 and b > 250:
        return False
    return abs(r - 245) < tol and abs(g - 241) < tol and abs(b - 232) < 36 and r > 200


def is_gold(rgb):
    r, g, b = rgb
    return r > 210 and 120 <= g <= 210 and b < 90 and r - b > 90


def is_proofing(rgb):
    r, g, b = rgb
    return r > 140 and g < 110 and b < 110 and r - g > 40


def blobs(im: Image.Image, pred, min_area=800):
    w, h = im.size
    px = im.load()
    vis = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if vis[y][x] or not pred(px[x, y][:3]):
                continue
            stack = [(x, y)]
            vis[y][x] = True
            minx = maxx = x
            miny = maxy = y
            n = 0
            while stack:
                cx, cy = stack.pop()
                n += 1
                minx, maxx = min(minx, cx), max(maxx, cx)
                miny, maxy = min(miny, cy), max(maxy, cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not vis[ny][nx] and pred(px[nx, ny][:3]):
                        vis[ny][nx] = True
                        stack.append((nx, ny))
            bw, bh = maxx - minx + 1, maxy - miny + 1
            if n >= min_area and bw > 12 and bh > 12:
                out.append({"x": minx, "y": miny, "w": bw, "h": bh, "n": n})
    out.sort(key=lambda b: (b["x"], b["y"]))
    return out


def iou(a, b):
    ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
    bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
    ix1, iy1 = max(a["x"], b["x"]), max(a["y"], b["y"])
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    union = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / union if union else 0.0


def fit(im: Image.Image, tw: int, th: int) -> Image.Image:
    """Cover-crop to target 16:9 so a toolbar crop cannot letterbox the slide."""
    im = im.convert("RGB")
    w, h = im.size
    scale = max(tw / w, th / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - tw) // 2)
    top = max(0, (nh - th) // 2)
    return resized.crop((left, top, left + tw, top + th))


def title_gold(im: Image.Image):
    """Gold highlight behind a title substring — not header bars or diagram nodes.

    Restrict to the title strip (above colored card headers). Yellow Parallel
    headers and orange LLM fills otherwise false-positive as gold.
    """
    w, h = im.size
    y0, y1 = int(h * 0.04), int(h * 0.16)
    crop = im.crop((0, y0, w, y1))
    found = blobs(crop, is_gold, min_area=80)
    if not found:
        return None
    found = [
        b for b in found
        if b["w"] < w * 0.22
        and b["h"] < h * 0.08
        and (b["x"] + b["w"] / 2) > w * 0.2
        and (b["x"] + b["w"] / 2) < w * 0.8
    ]
    if not found:
        return None
    x1 = min(b["x"] for b in found)
    y1b = min(b["y"] for b in found) + y0
    x2 = max(b["x"] + b["w"] for b in found)
    y2 = max(b["y"] + b["h"] for b in found) + y0
    merged_w = x2 - x1
    if merged_w > w * 0.22:
        return None
    return {"x": x1, "y": y1b, "w": merged_w, "h": y2 - y1b}


def is_header_green(rgb):
    r, g, b = rgb
    return g > 120 and g > r + 25 and g > b + 15 and r < 140


def is_header_blue(rgb):
    r, g, b = rgb
    return b > 140 and b > r + 30 and r < 140


def is_header_yellow(rgb):
    r, g, b = rgb
    return r > 200 and g > 150 and b < 80


def is_header_red(rgb):
    r, g, b = rgb
    return r > 160 and r > g + 40 and r > b + 40 and g < 140


def header_bands(im: Image.Image, pred, min_w_frac=0.12, max_w_frac=0.55,
                 min_h_frac=0.03, max_h_frac=0.18):
    """Detect wide horizontal header bars by row density (not flood-fill).

    Flood-fill merges header + same-hue diagram borders into one tall blob.
    Row bands stay header-height even when the frame shares the header color.
    """
    w, h = im.size
    px = im.load()
    # Per-row: longest run of pred pixels + start x
    row_runs = []
    for y in range(h):
        best = (0, 0)  # length, start
        run = 0
        start = 0
        for x in range(w):
            if pred(px[x, y][:3]):
                if run == 0:
                    start = x
                run += 1
                if run > best[0]:
                    best = (run, start)
            else:
                run = 0
        row_runs.append(best)

    min_w = int(w * min_w_frac)
    bands = []
    y = 0
    while y < h:
        length, start = row_runs[y]
        if length < min_w:
            y += 1
            continue
        y0 = y
        x0, x1 = start, start + length
        while y < h and row_runs[y][0] >= min_w:
            length, start = row_runs[y]
            x0 = min(x0, start)
            x1 = max(x1, start + length)
            y += 1
        y1 = y
        bw, bh = x1 - x0, y1 - y0
        if (min_w_frac * w <= bw <= max_w_frac * w
                and min_h_frac * h <= bh <= max_h_frac * h
                and bw > bh * 1.5):
            # Count pixels in band for ranking
            n = sum(1 for yy in range(y0, y1)
                    for xx in range(x0, x1) if pred(px[xx, yy][:3]))
            bands.append({"x": x0, "y": y0, "w": bw, "h": bh, "n": n})
    return bands


def merge_vertical_bands(bands, gap_tol=40, x_iou_min=0.7):
    """Merge stacked bands that are the same header split by white title glyphs."""
    if not bands:
        return []
    bands = sorted(bands, key=lambda b: (b["y"], b["x"]))
    merged = []
    for b in bands:
        if not merged:
            merged.append(dict(b))
            continue
        prev = merged[-1]
        # horizontal overlap
        ix1 = max(prev["x"], b["x"])
        ix2 = min(prev["x"] + prev["w"], b["x"] + b["w"])
        ow = max(0, ix2 - ix1)
        x_overlap = ow / min(prev["w"], b["w"]) if min(prev["w"], b["w"]) else 0
        vertical_gap = b["y"] - (prev["y"] + prev["h"])
        if x_overlap >= x_iou_min and -2 <= vertical_gap <= gap_tol:
            x0 = min(prev["x"], b["x"])
            y0 = min(prev["y"], b["y"])
            x1 = max(prev["x"] + prev["w"], b["x"] + b["w"])
            y1 = max(prev["y"] + prev["h"], b["y"] + b["h"])
            merged[-1] = {
                "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0,
                "n": prev["n"] + b["n"],
            }
        else:
            merged.append(dict(b))
    return merged


def cards(im: Image.Image):
    """Detect cards via colored header bars (any deck), then cream fallback.

    Prefer row-band headers so same-hue diagram borders do not swallow the bar.
    Merge bands stacked through white header text (one physical header → one bar).
    """
    w, h = im.size
    bars = []
    for pred in (is_header_green, is_header_blue, is_header_yellow, is_header_red):
        bars.extend(merge_vertical_bands(header_bands(im, pred)))
    bars.sort(key=lambda b: b["n"], reverse=True)
    kept = []
    for b in bars:
        if any(iou(b, k) > 0.35 for k in kept):
            continue
        kept.append(b)
        if len(kept) >= 6:
            break
    kept.sort(key=lambda b: (b["y"], b["x"]))
    if len(kept) >= 2:
        return kept
    # Fallback: old blob path (short bars only)
    blob_bars = []
    for pred in (is_header_green, is_header_blue, is_header_yellow, is_header_red):
        blob_bars.extend(blobs(im, pred, min_area=int(w * h * 0.003)))
    blob_bars = [
        b for b in blob_bars
        if b["w"] > w * 0.12 and b["w"] < w * 0.55
        and b["h"] < h * 0.18 and b["h"] > h * 0.03
        and b["w"] > b["h"] * 1.5
    ]
    blob_bars.sort(key=lambda b: b["n"], reverse=True)
    kept = []
    for b in blob_bars:
        if any(iou(b, k) > 0.35 for k in kept):
            continue
        kept.append(b)
        if len(kept) >= 6:
            break
    kept.sort(key=lambda b: (b["y"], b["x"]))
    if len(kept) >= 2:
        return kept
    found = blobs(im, is_cream, min_area=int(w * h * 0.015))
    return [
        b for b in found
        if b["h"] > h * 0.15 and b["w"] > w * 0.08
        and b["w"] < w * 0.7 and b["h"] < h * 0.7
    ]


def mean_abs(a: Image.Image, b: Image.Image, mask_proofing=True) -> float:
    w, h = a.size
    pa, pb = a.load(), b.load()
    s = 0
    n = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            ra, ga, ba = pa[x, y]
            if mask_proofing and is_proofing((ra, ga, ba)):
                continue
            rb, gb, bb = pb[x, y]
            s += abs(ra - rb) + abs(ga - gb) + abs(ba - bb)
            n += 1
    return s / (3 * n) if n else 999.0


def side_by_side(orig, rend, report, out_path: Path):
    w, h = orig.size
    gap = 16
    canvas = Image.new("RGB", (w * 2 + gap, h + 48), (24, 24, 24))
    canvas.paste(orig, (0, 48))
    canvas.paste(rend, (w + gap, 48))
    d = ImageDraw.Draw(canvas)
    d.text((12, 12), "ORIGINAL", fill=(255, 255, 255))
    d.text((w + gap + 12, 12), "POWERPOINT RENDER", fill=(255, 255, 255))
    # boxes
    for b in report.get("original_cards", []):
        d.rectangle([b["x"], b["y"] + 48, b["x"] + b["w"], b["y"] + b["h"] + 48],
                    outline=(0, 200, 80), width=2)
    for b in report.get("render_cards", []):
        d.rectangle([w + gap + b["x"], b["y"] + 48, w + gap + b["x"] + b["w"],
                     b["y"] + b["h"] + 48], outline=(0, 200, 80), width=2)
    hg = report.get("original_highlight")
    if hg:
        d.rectangle([hg["x"], hg["y"] + 48, hg["x"] + hg["w"], hg["y"] + hg["h"] + 48],
                    outline=(255, 180, 0), width=2)
    hg = report.get("render_highlight")
    if hg:
        d.rectangle([w + gap + hg["x"], hg["y"] + 48, w + gap + hg["x"] + hg["w"],
                     hg["y"] + hg["h"] + 48], outline=(255, 180, 0), width=2)
    canvas.save(out_path)


def compare(original: Path, render: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    orig = fit(Image.open(original), 1600, 900)
    rend = fit(Image.open(render), 1600, 900)
    orig_cards = cards(orig)
    rend_cards = cards(rend)
    orig_hl = title_gold(orig)
    rend_hl = title_gold(rend)
    failures = []

    if not orig_cards and not rend_cards:
        # Centered compositions / marketing UI — no cream header cards.
        # Gate on pixel MAE + optional blue/gold highlight only.
        mae_only = mean_abs(orig, rend)
        if mae_only > 55:
            failures.append(
                f"centered layout pixel MAE={mae_only:.1f} > 55 — rebuild drifted from photo"
            )
        # skip card-count / quadrant failures by clearing the would-be errors path
    elif not orig_cards:
        failures.append("original has no cream cards — cannot compare layout")
    if orig_cards or rend_cards:
        if len(rend_cards) != len(orig_cards):
            failures.append(
                f"card count {len(rend_cards)} != original {len(orig_cards)}"
            )

    # stacked-at-origin: a render card in the top-left 12% while original cards are not
    orig_topleft = any(c["x"] < orig.size[0] * 0.12 and c["y"] < orig.size[1] * 0.18
                       for c in orig_cards)
    for c in rend_cards:
        if c["x"] < rend.size[0] * 0.12 and c["y"] < rend.size[1] * 0.18 and not orig_topleft:
            failures.append(
                "a grouped card rendered at the slide origin — DOUBLE_OFFSET grouping bug"
            )
            break

    W, H = orig.size
    def quadrant(b):
        cx = b["x"] + b["w"] / 2
        cy = b["y"] + b["h"] / 2
        return (int(cy >= H * 0.5), int(cx >= W * 0.5))

    orig_map = {quadrant(c): c for c in orig_cards}
    rend_map = {quadrant(c): c for c in rend_cards}
    ious = []
    for q, oc in orig_map.items():
        rc = rend_map.get(q)
        if rc is None:
            failures.append(f"render is missing the card in quadrant {q}")
            ious.append(0.0)
            continue
        ious.append(iou(oc, rc))
        ox = (oc["x"] + oc["w"] / 2) / W
        oy = (oc["y"] + oc["h"] / 2) / H
        rx = (rc["x"] + rc["w"] / 2) / W
        ry = (rc["y"] + rc["h"] / 2) / H
        if abs(ox - rx) > 0.06 or abs(oy - ry) > 0.06:
            failures.append(
                f"card quadrant {q} centroid drifted dx={ox - rx:.3f} dy={oy - ry:.3f}"
            )

    if orig_hl and rend_hl:
        hl_iou = iou(orig_hl, rend_hl)
        width_ratio = rend_hl["w"] / max(1, orig_hl["w"])
        # screenshot gold often includes proofing; render must not be much WIDER
        if rend_hl["w"] > orig.size[0] * 0.18:
            failures.append(
                f"highlight is {rend_hl['w']}px wide — likely covering extra glyphs"
            )
        if width_ratio > 1.35:
            failures.append(
                f"highlight {width_ratio:.2f}× original width — lock to the substring, not a gold blob"
            )
    elif orig_hl and not rend_hl:
        failures.append("original has a title highlight; render does not")
    else:
        hl_iou = None
        width_ratio = None

    mae = mean_abs(orig, rend)
    report = {
        "passed": not failures,
        "failures": failures,
        "card_count_original": len(orig_cards),
        "card_count_render": len(rend_cards),
        "card_ious": [round(x, 3) for x in ious],
        "min_card_iou": round(min(ious), 3) if ious else 0,
        "highlight_iou": None if orig_hl is None or rend_hl is None else round(iou(orig_hl, rend_hl), 3),
        "highlight_width_ratio": None if width_ratio is None else round(width_ratio, 3),
        "pixel_mae": round(mae, 2),
        "original_cards": orig_cards,
        "render_cards": rend_cards,
        "original_highlight": orig_hl,
        "render_highlight": rend_hl,
    }
    side = out_dir / "compare_side_by_side.png"
    side_by_side(orig, rend, report, side)
    diff = ImageChops.difference(orig, rend)
    diff.save(out_dir / "compare_diff.png")
    (out_dir / "compare_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    report["side_by_side"] = str(side)
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--original", required=True)
    p.add_argument("--render", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    orig, rend = Path(args.original), Path(args.render)
    if not orig.exists() or not rend.exists():
        print("ERROR: original or render PNG missing")
        sys.exit(1)
    report = compare(orig, rend, Path(args.out))
    print("=" * 56)
    print("VISUAL COMPARE (PowerPoint render vs original)")
    print("=" * 56)
    print(f"  cards   orig={report['card_count_original']}  render={report['card_count_render']}"
          f"  min IoU={report['min_card_iou']}")
    print(f"  highlight IoU={report['highlight_iou']}  width ratio={report['highlight_width_ratio']}")
    print(f"  pixel MAE={report['pixel_mae']}")
    for f in report["failures"]:
        print(f"          - {f}")
    print("-" * 56)
    print("OVERALL:", "PASSED" if report["passed"] else "FAILED")
    print(f"Side-by-side: {report['side_by_side']}")
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
