#!/usr/bin/env python3
"""Regional (ROI) pixel compare — catch local drift that global MAE hides."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow is required"); sys.exit(1)

def mae_roi(a, b, box, step=2):
    x, y, w, h = [int(v) for v in box]
    pa, pb = a.load(), b.load()
    s = n = 0
    for yy in range(y, min(a.size[1], y + h), step):
        for xx in range(x, min(a.size[0], x + w), step):
            ra, ga, ba = pa[xx, yy]
            rb, gb, bb = pb[xx, yy]
            s += abs(ra - rb) + abs(ga - gb) + abs(ba - bb)
            n += 1
    return s / (3 * n) if n else 999.0

def fit_render_to_original(orig, rend):
    if rend.size == orig.size:
        return rend.convert("RGB")
    return rend.convert("RGB").resize(orig.size, Image.Resampling.LANCZOS)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--original", required=True)
    p.add_argument("--render", required=True)
    p.add_argument("--rois", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--overlay", default=None)
    args = p.parse_args()
    orig = Image.open(args.original).convert("RGB")
    rend = fit_render_to_original(orig, Image.open(args.render))
    rois = (json.loads(Path(args.rois).read_text()).get("rois") or [])
    if not rois:
        print("ERROR: rois.json has no rois"); sys.exit(1)
    failures, results = [], []
    for roi in rois:
        name = roi.get("name", "roi")
        box = roi["box"]
        max_mae = float(roi.get("max_mae", 40))
        score = mae_roi(orig, rend, box)
        rec = {"name": name, "box": box, "mae": round(score, 2), "max_mae": max_mae}
        results.append(rec)
        if score > max_mae:
            failures.append(f"{name}: ROI MAE {score:.1f} > {max_mae}")
    report = {"passed": not failures, "failures": failures, "rois": results}
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    overlay_path = Path(args.overlay) if args.overlay else out.with_suffix(".png")
    vis = Image.new("RGB", (orig.size[0] * 2 + 8, orig.size[1]), (20, 20, 20))
    vis.paste(orig, (0, 0)); vis.paste(rend, (orig.size[0] + 8, 0))
    d = ImageDraw.Draw(vis)
    for rec in results:
        x, y, w, h = rec["box"]
        color = (0, 220, 100) if rec["mae"] <= rec["max_mae"] else (255, 80, 80)
        d.rectangle([x, y, x + w, y + h], outline=color, width=2)
        d.rectangle([orig.size[0] + 8 + x, y, orig.size[0] + 8 + x + w, y + h], outline=color, width=2)
        d.text((x + 4, max(0, y - 12)), f"{rec["name"]} {rec["mae"]}", fill=color)
    vis.save(overlay_path)
    print("=" * 56); print("ROI COMPARE (regional MAE)"); print("=" * 56)
    for rec in results:
        flag = "OK" if rec["mae"] <= rec["max_mae"] else "FAIL"
        print(f"  [{flag}] {rec["name"]}: MAE={rec["mae"]} (max {rec["max_mae"]})")
    for f in failures: print(f"          - {f}")
    print("-" * 56)
    print("OVERALL:", "PASSED" if report["passed"] else "FAILED")
    print(f"Report: {out}"); print(f"Overlay: {overlay_path}")
    sys.exit(0 if report["passed"] else 1)

if __name__ == "__main__":
    main()
