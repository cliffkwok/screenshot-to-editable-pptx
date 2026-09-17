#!/usr/bin/env python3
"""Measure a nested row pack: dashed/stroked host + N equal children + pads/gaps.

Problem this solves
-------------------
Eyeballing padding inside a dashed host places children wrong. Instead:

  1. Detect child body boxes (vertical stroke runs).
  2. Detect host from top dashed envelope + bottom span *below labels*.
  3. Record pad_L/T/R/B, uniform body_w/h, hgap.
  4. Rebuild: body[i] = (host.x+pad_L+i*(body_w+hgap), host.y+pad_T, body_w, body_h)
  5. Badge sits *inside* body near top (measure pad_T_badge); labels use label_gap under body.

Usage
-----
  python3 scripts/measure_nested_pack.py \\
      --image shot.png --region 15,95,310,255 --name docsL \\
      --out nest.json --overlay nest.png
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from helpers import (  # noqa: E402
    pads_in_parent,
    nested_row_from_pads,
    badge_inside_body_top,
    measure_dashed_lines_under,
)


def is_w(c, thr=170):
    return c[0] >= thr and c[1] >= thr and c[2] >= thr


def longest_run(px, x, y0, y1, thr=170):
    best = (0, None, None)
    run = 0
    start = None
    for y in range(y0, y1):
        if is_w(px[x, y], thr):
            if run == 0:
                start = y
            run += 1
            if run > best[0]:
                best = (run, start, y)
        else:
            run = 0
            start = None
    return best


def edge_clusters(px, region, thr=170, min_run=55):
    x0, y0, x1, y1 = region
    cols = []
    for x in range(x0, x1):
        ln, a, b = longest_run(px, x, y0, y1, thr)
        if ln >= min_run:
            cols.append((x, ln, a, b))
    if not cols:
        return []
    groups = [[cols[0]]]
    for c in cols[1:]:
        if c[0] - groups[-1][-1][0] <= 2:
            groups[-1].append(c)
        else:
            groups.append([c])
    edges = []
    for g in groups:
        best = max(g, key=lambda t: t[1])
        edges.append(
            {"xL": g[0][0], "xR": g[-1][0], "run": best[1], "y0": best[2], "y1": best[3]}
        )
    return edges


def pair_bodies(edges, wmin=47, wmax=52):
    bodies = []
    used = set()
    for i, e in enumerate(edges):
        if i in used:
            continue
        for j in range(i + 1, len(edges)):
            if j in used:
                continue
            L, R = e["xL"], edges[j]["xR"]
            w = R - L + 1
            if wmin <= w <= wmax:
                y0 = max(e["y0"], edges[j]["y0"])
                y1 = min(e["y1"], edges[j]["y1"])
                if y1 - y0 + 1 < 50:
                    y0 = min(e["y0"], edges[j]["y0"])
                    y1 = max(e["y1"], edges[j]["y1"])
                bodies.append((L, y0, w, y1 - y0 + 1))
                used.add(i)
                used.add(j)
                break
    return sorted(bodies, key=lambda b: b[0])


def row_envelope(px, y, x0, x1, thr=150, min_count=40):
    xs = [x for x in range(x0, x1) if is_w(px[x, y], thr)]
    if len(xs) < min_count:
        return None
    return (min(xs), max(xs), max(xs) - min(xs) + 1, len(xs))


def _dashed_v_edge(px, x_lo, x_hi, y0, y1, thr=140, min_n=20, min_runs=6):
    """Leftmost or densest vertical dashed column in [x_lo,x_hi).

    Solid body walls have few runs; dashed host walls have many short runs.
    Do NOT use the top horizontal dash min/max x — rounded corners clip that
    span inward and falsely report pad_L/R ≈ 0–2 when the eye sees ~15–20px.
    """
    best = None  # (score, x, n, runs)
    for x in range(x_lo, x_hi):
        n = runs = 0
        inrun = False
        for y in range(y0, y1):
            v = is_w(px[x, y], thr)
            if v:
                n += 1
            if v and not inrun:
                runs += 1
                inrun = True
            elif not v:
                inrun = False
        if n >= min_n and runs >= min_runs:
            score = n + runs * 3
            if best is None or score > best[0]:
                best = (score, x, n, runs)
    return best[1] if best else None


def measure_host(px, bodies, region):
    """Top/bottom from dashed horizontal spans; L/R from vertical dashed walls."""
    bx0 = min(b[0] for b in bodies)
    bx1 = max(b[0] + b[2] for b in bodies)
    by0 = min(b[1] for b in bodies)
    by1 = max(b[1] + b[3] for b in bodies)
    x0, y0, x1, y1 = region
    min_w = int((bx1 - bx0) * 0.9)

    tops = []
    for y in range(max(y0, by0 - 30), by0):
        env = row_envelope(px, y, x0, x1)
        if env and env[2] >= min_w:
            tops.append((y, *env))
    bots = []
    # Search well below bodies so labels stay *inside* host
    for y in range(by1, y1):
        env = row_envelope(px, y, x0, x1)
        if env and env[2] >= min_w:
            bots.append((y, *env))
    if not tops or not bots:
        raise ValueError(f"host spans missing tops={len(tops)} bots={len(bots)}")
    top_y = tops[0][0]
    bot_y = bots[-1][0]  # last wide span = true dashed bottom (below labels)

    # Vertical dashed walls OUTSIDE the body cluster (the real host L/R)
    L = _dashed_v_edge(px, x0, bx0, top_y, bot_y + 1)
    R = _dashed_v_edge(px, bx1, x1, top_y, bot_y + 1)
    if L is None or R is None:
        # Fallback: top-row envelope (underestimates pad on rounded hosts)
        L, R = tops[0][1], tops[0][2]
        print(
            f"WARNING: dashed v-edge miss L={L} R={R}; "
            "using top-row envelope (pads may look too tight)"
        )
    return (L, top_y, R - L + 1, bot_y - top_y + 1)


def badge_inside(px, body, W, H):
    """Find badge diameter + top inset *inside* the body (not edge-docked).

    Circles sit fully inside the rect near the top — do not assume cy=body.top.
    Returns (diameter, pad_T_from_body_top).
    """
    bx, by, bw, bh = body
    cx = bx + bw / 2.0
    best = None  # score, d, cy
    cands = []
    for d in range(18, 28):
        for cy in range(by + d // 2, by + min(bh // 2, d + 12)):
            ring = tot = 0
            for yy in range(int(cy - d / 2) - 1, int(cy + d / 2) + 2):
                for xx in range(int(cx - d / 2) - 1, int(cx + d / 2) + 2):
                    dist = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                    if abs(dist - d / 2) <= 1.3:
                        tot += 1
                        if 0 <= xx < W and 0 <= yy < H and is_w(px[xx, yy], 150):
                            ring += 1
            sc = ring / max(tot, 1)
            cands.append((sc, d, cy))
    if not cands:
        return 22, 6.0
    cands.sort(key=lambda t: (-t[0], -t[1]))
    top = cands[0][0]
    # Among near-best rings, prefer larger diameter (matches photo circle ink)
    pool = [c for c in cands if c[0] >= top - 0.03]
    pool.sort(key=lambda t: (-t[1], -t[0]))
    _sc, d, cy = pool[0]
    pad_T = round(cy - d / 2.0 - by, 1)
    return d, max(0.0, pad_T)


def measure_inner_lines(px, body, badge_box, expect_n=3):
    """Dashed content lines under a badge — delegates to helpers (any screenshot)."""
    badge_bot = float(badge_box[1]) + float(badge_box[3])
    out = measure_dashed_lines_under(px, body, badge_bot, expect_n=expect_n)
    if not out:
        return None
    # nest JSON key name kept for existing builds
    out = dict(out)
    out["badge_to_line0"] = out.pop("anchor_to_line0")
    return out


def label_under(px, body, host, W, H):
    bx, by, bw, bh = body
    hy2 = host[1] + host[3]
    ink = []
    for y in range(by + bh + 2, min(H, hy2 - 2)):
        xs = [
            x
            for x in range(max(0, bx - 22), min(W, bx + bw + 22))
            if is_w(px[x, y], 140)
        ]
        if len(xs) >= 3:
            for x in xs:
                ink.append((x, y))
    if not ink:
        return None, None
    xs = [p[0] for p in ink]
    ys = [p[1] for p in ink]
    lab = (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    return lab, lab[1] - (by + bh)


def measure_pack(im, region, thr=170, expect_n=3):
    px = im.load()
    W, H = im.size
    edges = edge_clusters(px, region, thr=thr, min_run=55)
    bodies = pair_bodies(edges)
    if len(bodies) < expect_n:
        edges = edge_clusters(px, region, thr=thr, min_run=45)
        bodies = pair_bodies(edges)
    if len(bodies) != expect_n:
        raise ValueError(f"expected {expect_n} bodies, got {len(bodies)}: {bodies}")

    host = measure_host(px, bodies, region)
    bw = round(sum(b[2] for b in bodies) / expect_n)
    bh = round(sum(b[3] for b in bodies) / expect_n)
    hgaps = [
        bodies[i + 1][0] - (bodies[i][0] + bodies[i][2]) for i in range(expect_n - 1)
    ]
    hgap = round(sum(hgaps) / len(hgaps))
    pad_L = pads_in_parent(host, bodies[0])["pad_L"]
    pad_R = pads_in_parent(host, bodies[-1])["pad_R"]
    pad_T = round(
        sum(pads_in_parent(host, b)["pad_T"] for b in bodies) / expect_n, 1
    )
    pad_B = round(
        sum(pads_in_parent(host, b)["pad_B"] for b in bodies) / expect_n, 1
    )

    rebuilt = nested_row_from_pads(
        host, pad_L=pad_L, pad_T=pad_T, body_w=bw, body_h=bh, hgap=hgap, n=expect_n
    )

    children = []
    inner_gaps = []
    inter_gaps = []
    line_fracs_acc = []
    for i, b in enumerate(bodies):
        d, badge_pad_T = badge_inside(px, b, W, H)
        badge = badge_inside_body_top(b, d, pad_T=badge_pad_T)
        lab, lg = label_under(px, b, host, W, H)
        inner = measure_inner_lines(px, b, badge, expect_n=3)
        err = max(abs(rebuilt[i][k] - b[k]) for k in range(4))
        child = {
            "body_measured": list(map(int, b)),
            "body_from_pads": list(rebuilt[i]),
            "pads_in_host": pads_in_parent(host, b),
            "badge": [round(v, 1) for v in badge],
            "badge_d": d,
            "badge_pad_T": badge_pad_T,
            "label": list(map(int, lab)) if lab else None,
            "label_gap": lg,
            "inner_lines": inner,
            "rebuild_err_px": err,
        }
        children.append(child)
        if inner:
            inner_gaps.append(inner["badge_to_line0"])
            if inner["inter_line_gap"] is not None:
                inter_gaps.append(inner["inter_line_gap"])
            line_fracs_acc.append(inner["line_y_fracs"])

    badge_pads = [c["badge_pad_T"] for c in children]
    # Consensus inner-line layout across siblings (same icon family)
    line_y_fracs = None
    if line_fracs_acc:
        nL = len(line_fracs_acc[0])
        line_y_fracs = [
            round(sum(row[j] for row in line_fracs_acc) / len(line_fracs_acc), 3)
            for j in range(nL)
        ]
    x0f = x1f = None
    inners = [c["inner_lines"] for c in children if c["inner_lines"]]
    if inners:
        x0f = round(sum(i["line_x0_frac"] for i in inners) / len(inners), 3)
        x1f = round(sum(i["line_x1_frac"] for i in inners) / len(inners), 3)

    return {
        "region": list(region),
        "host": list(map(int, host)),
        "pad_L": pad_L,
        "pad_T": pad_T,
        "pad_R": pad_R,
        "pad_B": pad_B,
        "body_w": bw,
        "body_h": bh,
        "hgap": hgap,
        "badge_d": max(c["badge_d"] for c in children),
        "badge_pad_T": round(sum(badge_pads) / expect_n, 1),
        "badge_to_line0": round(sum(inner_gaps) / len(inner_gaps), 1) if inner_gaps else None,
        "inter_line_gap": round(sum(inter_gaps) / len(inter_gaps), 1) if inter_gaps else None,
        "line_y_fracs": line_y_fracs,
        "line_x0_frac": x0f,
        "line_x1_frac": x1f,
        "n_lines": len(line_y_fracs) if line_y_fracs else 0,
        "label_gap": round(
            sum(c["label_gap"] or 0 for c in children) / expect_n
        ),
        "children": children,
        "formula": (
            f"body[i]=(host.x+{pad_L}+i*({bw}+{hgap}), "
            f"host.y+{pad_T}, {bw}, {bh})"
        ),
        "max_rebuild_err_px": max(c["rebuild_err_px"] for c in children),
    }


def draw_overlay(im, region, pack, path):
    ov = im.crop(region).copy()
    dr = ImageDraw.Draw(ov)
    ox, oy = region[0], region[1]
    hx, hy, hw, hh = pack["host"]
    dr.rectangle(
        [hx - ox, hy - oy, hx + hw - ox, hy + hh - oy], outline=(255, 60, 60), width=2
    )
    for c in pack["children"]:
        bx, by, bw, bh = c["body_from_pads"]
        dr.rectangle(
            [bx - ox, by - oy, bx + bw - ox, by + bh - oy],
            outline=(255, 200, 0),
            width=2,
        )
        b = c["badge"]
        dr.ellipse(
            [b[0] - ox, b[1] - oy, b[0] + b[2] - ox, b[1] + b[3] - oy],
            outline=(80, 160, 255),
            width=2,
        )
        if c["label"]:
            lx, ly, lw, lh = c["label"]
            dr.rectangle(
                [lx - ox, ly - oy, lx + lw - ox, ly + lh - oy],
                outline=(255, 255, 0),
                width=1,
            )
    ov.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", required=True)
    ap.add_argument("--region", required=True, help="x0,y0,x1,y1")
    ap.add_argument("--name", default="pack")
    ap.add_argument("--thr", type=int, default=170)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--out", default="")
    ap.add_argument("--overlay", default="")
    args = ap.parse_args()

    region = tuple(int(v) for v in args.region.split(","))
    im = Image.open(args.image).convert("RGB")
    pack = measure_pack(im, region, thr=args.thr, expect_n=args.n)
    pack["name"] = args.name
    print(json.dumps({k: pack[k] for k in pack if k != "children"}, indent=2))
    print("children:")
    for c in pack["children"]:
        print(
            f"  body={c['body_measured']} from_pads={c['body_from_pads']} "
            f"err={c['rebuild_err_px']} badge_d={c['badge_d']} lab_gap={c['label_gap']}"
        )
    if pack["max_rebuild_err_px"] > 2:
        print(f"WARNING: rebuild err {pack['max_rebuild_err_px']}px > 2")
        sys.exit(2)
    if args.out:
        Path(args.out).write_text(json.dumps(pack, indent=2))
        print("wrote", args.out)
    if args.overlay:
        draw_overlay(im, region, pack, args.overlay)
        print("overlay", args.overlay)


if __name__ == "__main__":
    main()
