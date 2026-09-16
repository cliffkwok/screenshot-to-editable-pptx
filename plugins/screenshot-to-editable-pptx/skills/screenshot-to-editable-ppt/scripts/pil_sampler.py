#!/usr/bin/env python3
"""Extract exact hex colors from a screenshot. Never guess.

Usage:
  python3 pil_sampler.py --image screenshot.png --coords "(342,156) (420,510)" --out colors.json
  python3 pil_sampler.py --image screenshot.png --regions "card:100,100,200,150 badge:300,50,80,40" --out colors.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required. Install: pip install Pillow")
    sys.exit(1)


def parse_coords(s: str):
    matches = re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", s)
    return [(int(x), int(y)) for x, y in matches]


def parse_regions(s: str):
    regions = {}
    for item in s.split():
        m = re.match(r"(\w+):(\d+),(\d+),(\d+),(\d+)", item)
        if m:
            regions[m.group(1)] = (
                int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
            )
    return regions


def sample_point(img: Image.Image, x: int, y: int, retries=True):
    w, h = img.size
    if not (0 <= x < w and 0 <= y < h):
        return None
    r, g, b = img.getpixel((x, y))[:3]
    record = {
        "rgb": [r, g, b],
        "hex": f"#{r:02X}{g:02X}{b:02X}",
        "sampled_at": [x, y],
        "confidence": "direct_center",
    }
    if retries and (r, g, b) == (255, 255, 255):
        for dx, dy in ((5, 0), (-5, 0), (0, 5), (0, -5), (5, 5)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                rr, gg, bb = img.getpixel((nx, ny))[:3]
                if (rr, gg, bb) != (255, 255, 255):
                    record = {
                        "rgb": [rr, gg, bb],
                        "hex": f"#{rr:02X}{gg:02X}{bb:02X}",
                        "sampled_at": [nx, ny],
                        "requested_at": [x, y],
                        "confidence": "offset_retry",
                        "note": "Original coord was white; resampled nearby",
                    }
                    break
    return record


def sample_region(img: Image.Image, name: str, x: int, y: int, width: int, height: int):
    points = [
        (x + width // 2, y + height // 2),
        (x + width // 4, y + height // 4),
        (x + 3 * width // 4, y + 3 * height // 4),
    ]
    samples = []
    for px, py in points:
        s = sample_point(img, px, py, retries=False)
        if s:
            samples.append(s)
    if not samples:
        return None
    # Majority hex (not average — averaging muddies brand colors)
    from collections import Counter
    hexes = [s["hex"] for s in samples]
    winner = Counter(hexes).most_common(1)[0][0]
    chosen = next(s for s in samples if s["hex"] == winner)
    return {
        "name": name,
        "rgb": chosen["rgb"],
        "hex": winner,
        "region": [x, y, width, height],
        "sampled_points": [s["sampled_at"] for s in samples],
        "confidence": "region_majority",
    }


def main():
    parser = argparse.ArgumentParser(description="Extract exact colors from screenshot images")
    parser.add_argument("--image", required=True)
    parser.add_argument("--coords", default="")
    parser.add_argument("--regions", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"ERROR: Image not found: {img_path}")
        sys.exit(1)

    img = Image.open(img_path).convert("RGB")
    results = []

    if args.coords:
        for x, y in parse_coords(args.coords):
            record = sample_point(img, x, y)
            results.append(record or {"sampled_at": [x, y], "error": "out_of_bounds"})

    if args.regions:
        for name, box in parse_regions(args.regions).items():
            record = sample_region(img, name, *box)
            results.append(record or {"name": name, "region": list(box), "error": "out_of_bounds"})

    if not results:
        print("ERROR: Provide --coords and/or --regions")
        sys.exit(1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved {len(results)} color records to {out_path}")


if __name__ == "__main__":
    main()
