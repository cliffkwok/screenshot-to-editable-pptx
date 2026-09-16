#!/usr/bin/env python3
"""Rasterize a PPTX slide the way PowerPoint actually draws it.

Quick Look and `save as PNG` are not valid: QL drops groups, and AppleScript
`save as PNG` often just renames the .pptx. On macOS we open the file, start a
slideshow, screenshot, then crop the presenter toolbar.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required")
    sys.exit(1)


def osascript(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["osascript", "-e", script], capture_output=True, text=True)


def crop_toolbar(im: Image.Image) -> Image.Image:
    """Drop the slideshow popup toolbar along the bottom edge."""
    w, h = im.size
    rgb = im.convert("RGB")
    px = rgb.load()
    # Toolbar sits in the last ~5% and is not the slide fill.
    cut = h
    for y in range(h - 1, int(h * 0.88), -1):
        dark = 0
        for x in range(0, w, max(1, w // 80)):
            r, g, b = px[x, y]
            if r < 40 and g < 40 and b < 40:
                dark += 1
        # presenter chrome often has a dark strip; keep scanning
        if dark > 8:
            cut = y
            break
    # Always trim a little; Fit-to-Window chrome is shorter than slideshow chrome
    cut = min(cut, int(h * 0.97))
    if cut < h * 0.9:
        cut = int(h * 0.97)
    return im.crop((0, 0, w, cut))


def export_pptx(pptx: Path, out_png: Path) -> Path:
    pptx = pptx.resolve()
    out_png = out_png.resolve()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    raw = out_png.with_name(out_png.stem + ".raw.png")

    opened = osascript(f'''
tell application "Microsoft PowerPoint"
    activate
    close every presentation saving no
    open POSIX file "{pptx}"
    delay 1.2
    set ss to slide show settings of active presentation
    run slide show ss
end tell
''')
    if opened.returncode != 0:
        raise RuntimeError(f"PowerPoint slideshow failed: {opened.stderr.strip()}")
    time.sleep(1.4)

    cap = subprocess.run(
        ["screencapture", "-x", str(raw)],
        capture_output=True, text=True,
    )
    osascript('tell application "System Events" to key code 53')
    if cap.returncode != 0 or not raw.exists():
        raise RuntimeError(f"screencapture failed: {cap.stderr}")

    im = Image.open(raw)
    crop_toolbar(im).save(out_png)
    return out_png


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pptx", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    path = Path(args.pptx)
    if not path.exists():
        print(f"ERROR: PPTX not found: {path}")
        sys.exit(1)
    out = export_pptx(path, Path(args.out))
    print(f"Exported PowerPoint render → {out}")


if __name__ == "__main__":
    main()
