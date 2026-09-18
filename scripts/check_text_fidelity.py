#!/usr/bin/env python3
"""Fail-closed text fidelity gates: gaps, line-count, font weight.

Prevents the failure modes that checklists miss:
  - title↔subtitle gap collapsed in the PPT render
  - photo one-liner wrapped to 2 lines in PPT
  - Back/chrome forced bold when photo is regular

Usage:
  python3 scripts/check_text_fidelity.py \\
    --original work/.../original.png \\
    --render work/.../render.png \\
    --fidelity work/.../text_fidelity.json \\
    [--pptx work/.../out.pptx] \\
    --out work/.../text_fidelity_report.json
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


def ink_rows(px, x0, y0, x1, y1, thr: int) -> list[int]:
    rows = []
    for y in range(y0, y1 + 1):
        if any(px[x, y][0] < thr for x in range(x0, x1 + 1)):
            rows.append(y)
    return rows


def ink_bbox(px, box, thr: int):
    x, y, w, h = [int(v) for v in box]
    x0, y0, x1, y1 = x, y, x + w - 1, y + h - 1
    pts = [
        (xx, yy)
        for yy in range(y0, y1 + 1)
        for xx in range(x0, x1 + 1)
        if px[xx, yy][0] < thr
    ]
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def count_lines(px, box, thr: int, min_row_gap: int = 3) -> int:
    """Count horizontal ink bands inside box (approx line count)."""
    x, y, w, h = [int(v) for v in box]
    rows = ink_rows(px, x, y, x + w - 1, y + h - 1, thr)
    if not rows:
        return 0
    bands = 1
    for i in range(1, len(rows)):
        if rows[i] - rows[i - 1] > min_row_gap:
            bands += 1
    return bands


def map_box_to_render(box, ow, oh, rw, rh):
    x, y, w, h = box
    return [
        int(x * rw / ow),
        int(y * rh / oh),
        max(1, int(w * rw / ow)),
        max(1, int(h * rh / oh)),
    ]


def scale_gap_to_orig(gap_rend: int, oh: int, rh: int) -> float:
    return gap_rend * oh / rh


def check_pairs(orig, rend, pairs: list[dict], failures: list, details: list):
    op, rp = orig.load(), rend.load()
    ow, oh = orig.size
    rw, rh = rend.size
    for pair in pairs:
        name = pair.get("name", "pair")
        a = pair["a"]
        b = pair["b"]
        thr_a = int(a.get("thr", 80))
        thr_b = int(b.get("thr", 180))
        axis = pair.get("axis", "vertical")
        min_gap = float(pair.get("min_gap_px", 8))
        # Allow render gap to be slightly loose; never much tighter than photo.
        collapse_ratio = float(pair.get("collapse_ratio", 0.45))

        oa = ink_bbox(op, a["box"], thr_a)
        ob = ink_bbox(op, b["box"], thr_b)
        if oa is None or ob is None:
            failures.append(f"{name}: missing ink on original for text pair")
            continue
        if axis == "vertical":
            gap_o = ob[1] - (oa[1] + oa[3])
        else:
            gap_o = ob[0] - (oa[0] + oa[2])

        ra_box = map_box_to_render(a["box"], ow, oh, rw, rh)
        rb_box = map_box_to_render(b["box"], ow, oh, rw, rh)
        # Small pad only — do not expand into the sibling (false overlap).
        pad = max(1, int(3 * rw / ow))
        ra_box = [max(0, ra_box[0] - pad), max(0, ra_box[1] - pad),
                  ra_box[2] + 2 * pad, ra_box[3] + pad]  # no expand downward into B
        rb_box = [max(0, rb_box[0] - pad), rb_box[1],  # no expand upward into A
                  rb_box[2] + 2 * pad, rb_box[3] + 2 * pad]

        ra = ink_bbox(rp, ra_box, thr_a)
        rb = ink_bbox(rp, rb_box, thr_b)
        if ra is None or rb is None:
            failures.append(f"{name}: missing ink on render for text pair")
            continue
        if axis == "vertical":
            gap_r_px = rb[1] - (ra[1] + ra[3])
        else:
            gap_r_px = rb[0] - (ra[0] + ra[2])
        gap_r = scale_gap_to_orig(gap_r_px, oh, rh)

        rec = {
            "name": name,
            "gap_original_px": gap_o,
            "gap_render_px_orig_scale": round(gap_r, 2),
            "min_gap_px": min_gap,
        }
        details.append(rec)

        if gap_o < min_gap and gap_o >= 0:
            # photo itself is tight — still require render not worse than collapse_ratio of photo
            pass
        if gap_o > 0 and gap_r < gap_o * collapse_ratio:
            failures.append(
                f"{name}: text↔text gap collapsed "
                f"(original {gap_o}px → render ~{gap_r:.1f}px, "
                f"floor {gap_o * collapse_ratio:.1f}px)"
            )
        if gap_r < 0:
            failures.append(f"{name}: text bands overlap in render (gap={gap_r:.1f}px)")

        # Line counts
        for side, spec, o_box, r_box, thr in (
            ("a", a, a["box"], ra_box, thr_a),
            ("b", b, b["box"], rb_box, thr_b),
        ):
            want = spec.get("lines")
            if want is None:
                continue
            want = int(want)
            got_o = count_lines(op, o_box, thr)
            got_r = count_lines(rp, r_box, thr)
            rec[f"{side}_lines_original"] = got_o
            rec[f"{side}_lines_render"] = got_r
            if want == 1 and got_r > 1:
                failures.append(
                    f"{name}.{side}: photo expects 1 line but render has {got_r} "
                    f"(use wrap=False / widen box)"
                )
            if got_o == 1 and got_r > 1:
                failures.append(
                    f"{name}.{side}: original is 1 line, render wrapped to {got_r}"
                )


def check_weights(pptx: Path | None, weights: list[dict], failures: list, details: list):
    if not weights:
        return
    if pptx is None or not pptx.exists():
        failures.append("weights declared but --pptx missing")
        return
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pptx_inspect import inspect_pptx

    inspected = inspect_pptx(str(pptx), 0)
    shapes = inspected.get("shapes") or []
    by_name = {s.get("name"): s for s in shapes if s.get("name")}

    for w in weights:
        name = w.get("name") or w.get("element") or "weight"
        el = w.get("element") or w.get("name")
        expect = bool(w.get("expect_bold", False))
        target = by_name.get(el)
        if target is None:
            # search nested text
            for s in shapes:
                if s.get("name") == el:
                    target = s
                    break
        if target is None:
            failures.append(f"{name}: shape {el!r} not found for weight check")
            continue
        font = target.get("font") or {}
        runs = font.get("runs") or []
        if runs:
            got = bool(runs[0].get("bold"))
        else:
            got = bool(font.get("bold"))
        details.append({"name": name, "element": el, "expect_bold": expect, "actual_bold": got})
        if got != expect:
            failures.append(
                f"{name}: bold mismatch on {el!r} (expected {expect}, got {got})"
            )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", required=True)
    p.add_argument("--render", required=True)
    p.add_argument("--fidelity", required=True, help="text_fidelity.json")
    p.add_argument("--pptx", default=None)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    orig_path = Path(args.original)
    rend_path = Path(args.render)
    fid_path = Path(args.fidelity)
    if not orig_path.exists() or not rend_path.exists() or not fid_path.exists():
        print("ERROR: original, render, or fidelity JSON missing")
        sys.exit(1)

    fidelity = json.loads(fid_path.read_text())
    orig = Image.open(orig_path).convert("RGB")
    rend = Image.open(rend_path).convert("RGB")

    failures: list[str] = []
    details: list[dict] = []
    check_pairs(orig, rend, fidelity.get("text_pairs") or [], failures, details)
    check_weights(
        Path(args.pptx) if args.pptx else None,
        fidelity.get("weights") or [],
        failures,
        details,
    )

    report = {
        "passed": not failures,
        "failures": failures,
        "details": details,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))

    print("=" * 56)
    print("TEXT FIDELITY (gaps / lines / weight)")
    print("=" * 56)
    for d in details:
        print(f"  {d}")
    for f in failures:
        print(f"          - {f}")
    print("-" * 56)
    print("OVERALL:", "PASSED" if report["passed"] else "FAILED")
    print(f"Report: {out}")
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
