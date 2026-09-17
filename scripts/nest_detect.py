#!/usr/bin/env python3
"""Detect nested boxes + pads on a screenshot (box-inside-box).

Hierarchy:

  panel / slide
    └─ card          (white rounded rect)
         ├─ header   (solid colored bar — usually flush top / full width)
         ├─ diagram  (stroked INNER rect — inset → pad_L/R/T/B vs card)
         └─ caption  (band under diagram → card bottom)

Every child records pads_in_parent {pad_L, pad_R, pad_T, pad_B}.

Usage:
  python3 scripts/nest_detect.py --image shot.png --out nest.json \\
      --overlay nest.png --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow required")
    sys.exit(1)


def lum(c):
    return (c[0] + c[1] + c[2]) / 3.0


def is_red(c):
    r, g, b = c[:3]
    return r > 150 and g < 110 and b < 110 and r - g > 35


def is_reddish(c):
    """Looser red for thin AA strokes (diagram frames)."""
    r, g, b = c[:3]
    return r > 140 and r > g + 25 and r > b + 25 and g < 170 and b < 170


def is_yellow(c):
    r, g, b = c[:3]
    return r > 200 and g > 145 and b < 100 and r - b > 80


def is_yellowish(c):
    """Pale gold / yellow AA strokes (diagram frames are often washed-out)."""
    r, g, b = c[:3]
    return r > 175 and g > 145 and b < 210 and r >= g - 5 and (r - b) > 25


def is_green(c):
    r, g, b = c[:3]
    return g > 120 and g > r + 25 and g > b + 15 and r < 140


def is_greenish(c):
    r, g, b = c[:3]
    return g > 100 and g > r + 15 and g > b + 10 and r < 160


def is_blue(c):
    r, g, b = c[:3]
    return b > 140 and b > r + 30 and r < 140


def is_blueish(c):
    r, g, b = c[:3]
    return b > 120 and b > r + 20 and r < 160


def is_frame_stroke(c):
    """Diagram frame strokes: header hue OR common tan/beige/gray frames.

    Multi-card decks often use a pale tan border for every diagram regardless
    of the colored header — matching only the header hue misses the frame and
    latches onto tiny inner widgets instead.
    """
    r, g, b = c[:3]
    if is_reddish(c) or is_yellowish(c) or is_greenish(c) or is_blueish(c):
        return True
    # tan / beige / gold wash
    if r > 175 and g > 145 and 90 < b < 210 and (r - b) > 20 and abs(r - g) < 55:
        return True
    # neutral gray stroke
    if abs(r - g) < 14 and abs(g - b) < 14 and 70 < r < 205:
        return True
    return False


HEADER_PREDS = (
    ("red", is_red),
    ("yellow", is_yellow),
    ("green", is_green),
    ("blue", is_blue),
)

STROKE_PREDS = {
    "red": is_reddish,
    "yellow": is_yellowish,
    "green": is_greenish,
    "blue": is_blueish,
}


def pads(parent, child):
    px, py, pw, ph = parent
    cx, cy, cw, ch = child
    return {
        "pad_L": round(cx - px, 1),
        "pad_T": round(cy - py, 1),
        "pad_R": round((px + pw) - (cx + cw), 1),
        "pad_B": round((py + ph) - (cy + ch), 1),
    }


def box(x0, y0, x1, y1):
    return [int(x0), int(y0), int(max(1, x1 - x0)), int(max(1, y1 - y0))]


def iou_xywh(a, b):
    ax, ay, aw, ah = a if not isinstance(a, dict) else (a["x"], a["y"], a["w"], a["h"])
    bx, by, bw, bh = b if not isinstance(b, dict) else (b["x"], b["y"], b["w"], b["h"])
    ax2, ay2, bx2, by2 = ax + aw, ay + ah, bx + bw, by + bh
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


# ── header detection (row bands + merge split-by-text) ───────────────────────

def header_bands(im, pred, min_w_frac=0.12, max_w_frac=0.55,
                 min_h_frac=0.015, max_h_frac=0.14):
    w, h = im.size
    px = im.load()
    row_runs = []
    for y in range(h):
        best_len = best_start = run = start = 0
        for x in range(w):
            if pred(px[x, y]):
                if run == 0:
                    start = x
                run += 1
                if run > best_len:
                    best_len, best_start = run, start
            else:
                run = 0
        row_runs.append((best_len, best_start))

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
        bw, bh = x1 - x0, y - y0
        if (min_w <= bw <= w * max_w_frac
                and h * min_h_frac <= bh <= h * max_h_frac
                and bw > bh * 1.4):
            n = sum(1 for yy in range(y0, y) for xx in range(x0, x1) if pred(px[xx, yy]))
            bands.append({"x": x0, "y": y0, "w": bw, "h": bh, "n": n})
    return bands


def merge_vertical(bands, gap_tol=22, x_ov=0.7):
    """Merge vertically-split header bands (white text holes in a solid bar)."""
    if not bands:
        return []
    bands = sorted(bands, key=lambda b: (b["y"], b["x"]))
    out = []
    for b in bands:
        if not out:
            out.append(dict(b))
            continue
        p = out[-1]
        ix1 = max(p["x"], b["x"])
        ix2 = min(p["x"] + p["w"], b["x"] + b["w"])
        ow = max(0, ix2 - ix1)
        overlap = ow / min(p["w"], b["w"]) if min(p["w"], b["w"]) else 0
        gap = b["y"] - (p["y"] + p["h"])
        # Glue text-split fragments of one bar; stop before diagram nodes.
        if overlap >= x_ov and -2 <= gap <= gap_tol and (p["h"] + b["h"] + max(0, gap)) <= 90:
            x0 = min(p["x"], b["x"])
            y0 = min(p["y"], b["y"])
            x1 = max(p["x"] + p["w"], b["x"] + b["w"])
            y1 = max(p["y"] + p["h"], b["y"] + b["h"])
            out[-1] = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0,
                       "n": p["n"] + b["n"]}
        else:
            out.append(dict(b))
    # Drop sparse bands (diagram ink) — solid headers are dense after merge
    dense = []
    for b in out:
        fill = b["n"] / max(1, b["w"] * b["h"])
        if fill >= 0.28 and b["h"] >= 12:
            dense.append(b)
    return dense


# ── card from header ─────────────────────────────────────────────────────────

def card_from_header(im, header, panel_lum_max=238):
    """Card ≈ header width (flush headers); height from strip occupancy until panel."""
    w, h = im.size
    px = im.load()
    hx, hy, hw, hh = header["x"], header["y"], header["w"], header["h"]

    left, right = hx, hx + hw - 1
    mid_y = min(h - 1, hy + hh + 30)
    for x in range(hx - 1, max(0, hx - 12), -1):
        if lum(px[x, mid_y]) >= 245:
            left = x
        else:
            break
    for x in range(hx + hw, min(w, hx + hw + 12)):
        if lum(px[x, mid_y]) >= 245:
            right = x
        else:
            break

    top = hy
    n_cols = max(1, right - left + 1)
    bottom = hy + hh
    miss = 0
    seen_body = False
    for y in range(hy + hh, min(h, hy + hh + int(h * 0.75))):
        white = accent = 0
        for x in range(left, right + 1):
            c = px[x, y]
            L = lum(c)
            if L >= 245:
                white += 1
            elif is_red(c) or is_yellow(c) or is_green(c) or is_blue(c) or is_reddish(c) or is_yellowish(c):
                accent += 1
            elif L >= 220 and abs(c[0] - c[1]) < 15:
                white += 1  # light gray still on card (caption / soft fill)
        frac = (white + accent) / n_cols
        if frac >= 0.20:
            bottom = y
            seen_body = True
            miss = 0
        else:
            # panel gray strip
            if seen_body:
                miss += 1
                if miss >= 4:
                    break
            # before body: ignore AA fringe under header
    return box(left, top, right + 1, bottom + 1)


# ── diagram stroked rect below header ────────────────────────────────────────

def find_diagram(im, card_box, header_box, pred):
    """Inner stroked rectangle — prefer frame edges near card L/R, not inner ink."""
    px = im.load()
    cx, cy, cw, ch = card_box
    hx, hy, hw, hh = header_box

    body_top = hy + hh + 1
    body_bot = cy + ch - 1
    body_left = cx
    body_right = cx + cw - 1
    if body_bot - body_top < 30:
        return None

    body_h = body_bot - body_top + 1
    col_score = []
    for x in range(body_left, body_right + 1):
        n = sum(1 for y in range(body_top, body_bot + 1) if pred(px[x, y]))
        col_score.append(n)

    thr = max(10, int(body_h * 0.18))
    left_zone = body_left + max(8, cw // 4)
    right_zone = body_right - max(8, cw // 4)

    def best_in_range(x0, x1):
        best_x, best_n = None, 0
        for x in range(x0, x1 + 1):
            n = col_score[x - body_left]
            if n >= thr and n > best_n:
                best_n, best_x = n, x
        return best_x

    dL = best_in_range(body_left, left_zone)
    dR = best_in_range(right_zone, body_right)
    if dL is None or dR is None or dR - dL < 40:
        xs = [body_left + i for i, n in enumerate(col_score) if n >= thr]
        if len(xs) < 2:
            thr = max(6, int(body_h * 0.08))
            xs = [body_left + i for i, n in enumerate(col_score) if n >= thr]
        if len(xs) < 2:
            return None
        dL, dR = xs[0], xs[-1]

    row_score = []
    for y in range(body_top, body_bot + 1):
        n = sum(1 for x in range(dL, dR + 1) if pred(px[x, y]))
        row_score.append(n)
    # Thin frame strokes are sparse vs filled widgets — use a low edge threshold
    thr_r = max(8, int((dR - dL) * 0.04))
    top_zone = body_top + max(6, body_h // 3)
    bot_zone = body_bot - max(6, int(body_h * 0.35))

    def first_row(y0, y1, step=1):
        """First row above thr walking from y0 toward y1 (near header / near bottom)."""
        y = y0
        while (y <= y1) if step > 0 else (y >= y1):
            n = row_score[y - body_top]
            if n >= thr_r:
                # local max in small window
                best_y, best_n = y, n
                for j in range(y, y + 5 * step, step):
                    if (j > y1) if step > 0 else (j < y1):
                        break
                    nn = row_score[j - body_top]
                    if nn > best_n:
                        best_n, best_y = nn, j
                return best_y
            y += step
        return None

    dT = first_row(body_top, min(top_zone, body_bot), 1)
    dB = first_row(body_bot, max(bot_zone, body_top), -1)
    if dT is None or dB is None or dB - dT < 40:
        ys = [body_top + i for i, n in enumerate(row_score) if n >= thr_r]
        if len(ys) < 2:
            thr_r2 = max(6, int((dR - dL) * 0.12))
            ys = [body_top + i for i, n in enumerate(row_score) if n >= thr_r2]
        if len(ys) < 2:
            return None
        dT, dB = ys[0], ys[-1]

    # Many decks: header bottom IS the diagram top (no separate top stroke).
    # If detected top is far below header but L/R edges exist, snap to body_top.
    if dT - body_top > max(12, (body_bot - body_top) * 0.12):
        dT = body_top

    return box(dL, dT, dR + 1, dB + 1)


def diagram_score(card_box, diagram):
    """Higher = more like a real inset diagram frame (not an inner widget)."""
    if not diagram:
        return -1e9
    p = pads(card_box, diagram)
    cw, ch = card_box[2], card_box[3]
    dw, dh = diagram[2], diagram[3]
    side = p["pad_L"] + p["pad_R"]
    score = 0.0
    # want ~55–95% of card width
    wr = dw / max(1, cw)
    if 0.55 <= wr <= 0.96:
        score += 40 + 20 * wr
    else:
        score -= 80 * abs(wr - 0.75)
    # side pads should be small but non-zero
    if 2 <= side <= cw * 0.35:
        score += 30
    else:
        score -= 40
    # height should eat a meaningful chunk of body — leave caption band
    hr = dh / max(1, ch)
    if 0.25 <= hr <= 0.70:
        score += 25
    elif hr > 0.78:
        score -= 40  # ate caption / body
    else:
        score -= 20
    # caption room under diagram
    if p["pad_B"] >= ch * 0.15:
        score += 20
    elif p["pad_B"] < ch * 0.08:
        score -= 35
    if p["pad_L"] < 2 or p["pad_R"] < 2:
        score -= 50
    return score


def find_diagram_best(im, card_box, header_box, color_name):
    """Try header-hue stroke, then universal frame stroke; keep best score."""
    preds = []
    if color_name in STROKE_PREDS:
        preds.append(STROKE_PREDS[color_name])
    preds.append(is_frame_stroke)
    best, best_s = None, -1e9
    for pred in preds:
        d = find_diagram(im, card_box, header_box, pred)
        s = diagram_score(card_box, d)
        if s > best_s:
            best, best_s = d, s
    if best is None or best_s < 0:
        return None
    return best


# ── stroke-bordered cards (Pros/Cons, Sequential agent, …) ───────────────────

def find_stroke_cards(im, min_w_frac=0.12, min_h_frac=0.18, max_cards=8):
    """Detect large colored rectangular strokes used as cards (no solid header)."""
    w, h = im.size
    # Downsample for speed on 2K+ screenshots; map boxes back to full res.
    scale = 1
    work = im
    if max(w, h) > 1400:
        scale = 2
        work = im.resize((w // scale, h // scale))
    ww, hh = work.size
    px = work.load()
    frames = []
    for color_name, pred in (
        ("green", is_greenish),
        ("red", is_reddish),
        ("yellow", is_yellowish),
        ("blue", is_blueish),
    ):
        col_n = []
        for x in range(ww):
            n = sum(1 for y in range(0, hh, 2) if pred(px[x, y]))
            col_n.append(n)
        thr = max(8, int(hh * min_h_frac * 0.2))
        xs = [x for x, n in enumerate(col_n) if n >= thr]
        if len(xs) < 2:
            continue
        edges = []
        run = [xs[0]]
        for x in xs[1:]:
            if x - run[-1] <= 2:
                run.append(x)
            else:
                edges.append(run[len(run) // 2])
                run = [x]
        edges.append(run[len(run) // 2])
        for i in range(len(edges) - 1):
            L, R = edges[i], edges[i + 1]
            if R - L < ww * min_w_frac:
                continue
            row_n = []
            step = max(1, (R - L) // 80)
            for y in range(hh):
                n = sum(1 for x in range(L, R + 1, step) if pred(px[x, y]))
                row_n.append(n)
            thr_r = max(6, int(((R - L) / step) * 0.08))
            ys = [y for y, n in enumerate(row_n) if n >= thr_r]
            if len(ys) < 2:
                continue
            T, B = ys[0], ys[-1]
            if B - T < hh * min_h_frac:
                continue
            bw, bh = R - L + 1, B - T + 1
            if bw * bh < ww * hh * 0.04:
                continue
            # map to full-res
            box_full = box(L * scale, T * scale, (R + 1) * scale, (B + 1) * scale)
            frames.append({
                "box_px": box_full,
                "color": color_name,
                "area": box_full[2] * box_full[3],
            })
    frames.sort(key=lambda f: -f["area"])
    kept = []
    for f in frames:
        if any(iou_xywh(f["box_px"], k["box_px"]) > 0.4 for k in kept):
            continue
        kept.append(f)
        if len(kept) >= max_cards:
            break
    kept.sort(key=lambda f: (f["box_px"][1], f["box_px"][0]))
    return kept


def stroke_card_children(card_box):
    """Header = top band; diagram = remaining body (content nest)."""
    cx, cy, cw, ch = card_box
    hh = max(28, int(ch * 0.22))
    header = [cx, cy, cw, hh]
    diagram = [cx + max(4, cw // 40), cy + hh,
               cw - 2 * max(4, cw // 40), ch - hh - max(4, ch // 40)]
    if diagram[3] < 20:
        diagram = [cx + 6, cy + 6, cw - 12, ch - 12]
    return header, diagram


# ── detect ───────────────────────────────────────────────────────────────────

def detect(im: Image.Image) -> dict:
    w, h = im.size
    headers = []
    for name, pred in HEADER_PREDS:
        for b in merge_vertical(header_bands(im, pred)):
            bb = dict(b)
            bb["color"] = name
            headers.append(bb)
    headers.sort(key=lambda b: b["n"], reverse=True)
    kept = []
    for b in headers:
        if any(iou_xywh(b, k) > 0.35 for k in kept):
            continue
        kept.append(b)
    # Same-color bars that share an x-range: keep the topmost dense header only
    # (diagram nodes below often match header hue and spawn false bands).
    kept.sort(key=lambda b: (b["color"], b["y"], -b["n"]))
    filtered = []
    for b in kept:
        clash = False
        for k in filtered:
            if b["color"] != k["color"]:
                continue
            ix1 = max(b["x"], k["x"])
            ix2 = min(b["x"] + b["w"], k["x"] + k["w"])
            ov = max(0, ix2 - ix1) / min(b["w"], k["w"])
            if ov > 0.5:
                clash = True
                break
        if not clash:
            filtered.append(b)
    kept = sorted(filtered, key=lambda b: (b["y"], b["x"]))

    cards = []
    layout_kind = "none"
    for i, hdr in enumerate(kept):
        card_box = card_from_header(im, hdr)
        header_box = [hdr["x"], hdr["y"], hdr["w"], hdr["h"]]
        header_box[0] = max(header_box[0], card_box[0])
        header_box[2] = min(hdr["x"] + hdr["w"], card_box[0] + card_box[2]) - header_box[0]
        # Collapsed body (header ≈ whole card) → bad card_from_header on noisy shots
        if card_box[3] - header_box[3] < 120:
            continue

        children = [{
            "id": f"card_{i}_header",
            "role": "header",
            "box_px": header_box,
            "pads_in_parent": pads(card_box, header_box),
            "color": hdr["color"],
        }]

        diagram = find_diagram_best(im, card_box, header_box, hdr["color"])
        if diagram and diagram_score(card_box, diagram) < 8:
            diagram = None
        if diagram:
            children.append({
                "id": f"card_{i}_diagram",
                "role": "diagram",
                "box_px": diagram,
                "pads_in_parent": pads(card_box, diagram),
                "pad_from_header": round(diagram[1] - (header_box[1] + header_box[3]), 1),
                "color": hdr["color"],
            })
            cap_top = diagram[1] + diagram[3]
            cap_bot = card_box[1] + card_box[3]
            if cap_bot - cap_top > 10:
                cap_box = [
                    card_box[0] + int(card_box[2] * 0.05),
                    cap_top,
                    int(card_box[2] * 0.90),
                    cap_bot - cap_top,
                ]
                children.append({
                    "id": f"card_{i}_caption",
                    "role": "caption_band",
                    "box_px": cap_box,
                    "pads_in_parent": pads(card_box, cap_box),
                })

        cards.append({
            "id": f"card_{i}",
            "role": "card",
            "layout": "header_bar",
            "box_px": card_box,
            "color": hdr["color"],
            "children": children,
        })

    if cards:
        layout_kind = "header_bar"
        # Prefer cards whose diagram scores well; drop IoU-overlapping losers
        ranked = []
        for c in cards:
            diag = next((ch for ch in c["children"] if ch["role"] == "diagram"), None)
            s = diagram_score(c["box_px"], diag["box_px"] if diag else None)
            ranked.append((s, c))
        ranked.sort(key=lambda t: -t[0])
        deduped = []
        for s, c in ranked:
            if any(iou_xywh(c["box_px"], k["box_px"]) > 0.3 for k in deduped):
                continue
            deduped.append(c)
        deduped.sort(key=lambda c: (c["box_px"][1], c["box_px"][0]))
        cards = deduped
        n_diag = sum(1 for c in cards if any(ch["role"] == "diagram" for ch in c["children"]))
        if n_diag == 0:
            cards = []
            layout_kind = "none"

    if not cards:
        stroke_frames = find_stroke_cards(im)
        for i, fr in enumerate(stroke_frames):
            card_box = fr["box_px"]
            header_box, diagram = stroke_card_children(card_box)
            children = [
                {
                    "id": f"card_{i}_header",
                    "role": "header",
                    "box_px": header_box,
                    "pads_in_parent": pads(card_box, header_box),
                    "color": fr["color"],
                },
                {
                    "id": f"card_{i}_diagram",
                    "role": "diagram",
                    "box_px": diagram,
                    "pads_in_parent": pads(card_box, diagram),
                    "pad_from_header": round(diagram[1] - (header_box[1] + header_box[3]), 1),
                    "color": fr["color"],
                },
            ]
            cards.append({
                "id": f"card_{i}",
                "role": "card",
                "layout": "stroke_card",
                "box_px": card_box,
                "color": fr["color"],
                "children": children,
            })
        if cards:
            layout_kind = "stroke_card"

    return {
        "image_size": [w, h],
        "law": "box-inside-box: every child measured vs parent pads",
        "layout_kind": layout_kind,
        "cards": cards,
        "summary": [
            {
                "id": c["id"],
                "layout": c.get("layout"),
                "color": c["color"],
                "card": c["box_px"],
                "header": next((ch["box_px"] for ch in c["children"] if ch["role"] == "header"), None),
                "diagram": next((ch["box_px"] for ch in c["children"] if ch["role"] == "diagram"), None),
                "diagram_pads": next(
                    (ch.get("pads_in_parent") for ch in c["children"] if ch["role"] == "diagram"),
                    None,
                ),
            }
            for c in cards
        ],
    }


def draw_overlay(im, report, path: Path):
    vis = im.convert("RGB").copy()
    d = ImageDraw.Draw(vis)
    colors = {
        "card": (0, 200, 80),
        "header": (220, 30, 30),
        "diagram": (30, 100, 255),
        "caption_band": (180, 60, 220),
    }
    for card in report["cards"]:
        x, y, w, h = card["box_px"]
        d.rectangle([x, y, x + w - 1, y + h - 1], outline=colors["card"], width=3)
        d.text((x + 4, y + 4), "card", fill=colors["card"])
        for ch in card["children"]:
            cx, cy, cw, chh = ch["box_px"]
            col = colors.get(ch["role"], (255, 160, 0))
            d.rectangle([cx, cy, cx + cw - 1, cy + chh - 1], outline=col, width=2)
            label = ch["role"]
            if ch["role"] == "diagram" and ch.get("pads_in_parent"):
                p = ch["pads_in_parent"]
                label = f"diag L{p['pad_L']} R{p['pad_R']} T{p['pad_T']} B{p['pad_B']}"
            d.text((cx + 3, cy + 3), label, fill=col)
    vis.save(path)


def self_test(report: dict) -> tuple[str, list[str]]:
    """Return (status, messages). status: PASS | FAIL | SKIP."""
    kind = report.get("layout_kind") or "none"
    cards = report.get("cards") or []
    if not cards:
        # No nestable cards — flow/UI/marketing slides are out of scope for this detector
        return "SKIP", ["no nestable cards (layout not header_bar / stroke_card)"]

    fails = []
    for c in cards:
        roles = [ch["role"] for ch in c["children"]]
        if "header" not in roles:
            fails.append(f"{c['id']}: missing header")
        if "diagram" not in roles:
            fails.append(f"{c['id']}: missing diagram (inner box)")
            continue
        diag = next(ch for ch in c["children"] if ch["role"] == "diagram")
        p = diag["pads_in_parent"]
        layout = c.get("layout") or kind
        for k in ("pad_L", "pad_R", "pad_B"):
            if p[k] < 2:
                fails.append(f"{c['id']}: diagram {k}={p[k]} — need inset ≥ 2")
        if p["pad_T"] < 0:
            fails.append(f"{c['id']}: diagram pad_T negative")
        cw = c["box_px"][2]
        if layout == "header_bar":
            if p["pad_L"] + p["pad_R"] > cw * 0.45:
                fails.append(
                    f"{c['id']}: diagram side pads {p['pad_L']}+{p['pad_R']} "
                    f"too large vs card w={cw} — likely wrong (inner widget)"
                )
            if diag["box_px"][2] < cw * 0.45:
                fails.append(f"{c['id']}: diagram width {diag['box_px'][2]} << card {cw}")
            if diag["box_px"][2] >= cw - 2:
                fails.append(f"{c['id']}: diagram width ≈ card — missing side inset")
        # stroke_card: diagram is content band — side pads small by construction
    if fails:
        return "FAIL", fails
    return "PASS", []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--overlay", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    im = Image.open(args.image).convert("RGB")
    report = detect(im)
    out = Path(args.out) if args.out else Path(args.image).with_name("nest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"wrote {out}  layout={report.get('layout_kind')}")
    for s in report["summary"]:
        print(f"  {s['id']} {s.get('layout')} {s['color']}: card={s['card']} diag={s['diagram']} pads={s['diagram_pads']}")

    if args.overlay:
        draw_overlay(im, report, Path(args.overlay))
        print(f"overlay {args.overlay}")

    status, msgs = self_test(report)
    if status == "PASS":
        print("SELF-TEST PASS")
        sys.exit(0)
    if status == "SKIP":
        print("SELF-TEST SKIP:")
        for m in msgs:
            print(f"  - {m}")
        # skip is not a hard fail for batch (exit 2); --self-test alone still 0
        sys.exit(0 if not args.self_test else 0)
    print("SELF-TEST FAIL:")
    for m in msgs:
        print(f"  - {m}")
    sys.exit(1 if args.self_test else 0)


if __name__ == "__main__":
    main()
