#!/usr/bin/env python3
"""Rasterize a PPTX slide the way PowerPoint actually draws it.

Quick Look and `save as PNG` are not valid: QL drops groups, and AppleScript
`save as PNG` often just renames the .pptx. On macOS we open the file, start a
slideshow, screenshot the slideshow window (not the full desktop — Cursor/IDE
often sits on top), then crop the presenter toolbar.
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


def find_pptx_slideshow_window_id() -> int | None:
    """Return CGWindow id of the largest on-screen PowerPoint slideshow window."""
    swift = r'''
import Cocoa
let opts = CGWindowListOption(arrayLiteral: .optionOnScreenOnly, .excludeDesktopElements)
guard let info = CGWindowListCopyWindowInfo(opts, kCGNullWindowID) as? [[String: Any]] else { exit(1) }
var bestId = 0
var bestArea: CGFloat = 0
for w in info {
  let owner = (w[kCGWindowOwnerName as String] as? String) ?? ""
  guard owner.contains("PowerPoint") else { continue }
  let layer = (w[kCGWindowLayer as String] as? Int) ?? -1
  guard layer == 0 else { continue }
  let name = (w[kCGWindowName as String] as? String) ?? ""
  let b = (w[kCGWindowBounds as String] as? [String: Any]) ?? [:]
  let ww = (b["Width"] as? NSNumber)?.doubleValue ?? 0
  let hh = (b["Height"] as? NSNumber)?.doubleValue ?? 0
  let area = ww * hh
  let isShow = name.localizedCaseInsensitiveContains("slide show")
  // Prefer slideshow windows; otherwise take largest PPT window.
  let score = area + (isShow ? 1_000_000_000 : 0)
  if score > bestArea {
    bestArea = score
    bestId = (w[kCGWindowNumber as String] as? Int) ?? 0
  }
}
if bestId == 0 { exit(2) }
print(bestId)
'''
    r = subprocess.run(
        ["swift", "-e", swift],
        capture_output=True, text=True, timeout=90,
    )
    if r.returncode != 0:
        return None
    line = (r.stdout or "").strip().splitlines()
    if not line:
        return None
    try:
        return int(line[-1].strip())
    except ValueError:
        return None


def crop_toolbar(im: Image.Image) -> Image.Image:
    """Drop the slideshow popup toolbar along the bottom edge."""
    w, h = im.size
    rgb = im.convert("RGB")
    px = rgb.load()
    cut = h
    for y in range(h - 1, int(h * 0.88), -1):
        dark = 0
        for x in range(0, w, max(1, w // 80)):
            r, g, b = px[x, y]
            if r < 40 and g < 40 and b < 40:
                dark += 1
        if dark > 8:
            cut = y
            break
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
delay 0.5
tell application "System Events"
    set frontmost of process "Microsoft PowerPoint" to true
end tell
''')
    if opened.returncode != 0:
        raise RuntimeError(f"PowerPoint slideshow failed: {opened.stderr.strip()}")
    time.sleep(1.6)

    wid = find_pptx_slideshow_window_id()
    if wid:
        cap = subprocess.run(
            ["screencapture", "-x", "-l", str(wid), str(raw)],
            capture_output=True, text=True,
        )
        print(f"captured window id={wid}")
    else:
        # Last resort: full display (may grab IDE if focus stolen)
        print("WARN: no PPT window id; falling back to full-display capture")
        cap = subprocess.run(
            ["screencapture", "-x", str(raw)],
            capture_output=True, text=True,
        )

    osascript('tell application "System Events" to key code 53')
    if cap.returncode != 0 or not raw.exists():
        raise RuntimeError(f"screencapture failed: {cap.stderr}")

    im = Image.open(raw)
    # Reject Cursor/IDE grabs: those are mid-gray UI chrome, not a slide.
    # Dark decks (avg ~30–50) and light decks (avg ~200+) are both valid.
    sample = im.convert("RGB").resize((64, 36))
    pixels = list(sample.getdata())
    avg = [sum(c) / len(c) for c in zip(*pixels)]
    # IDE chrome often has strong horizontal structure + mid luminance;
    # real slides (light or dark) are more uniform in a coarse downsample.
    import statistics
    lum = [(r + g + b) / 3 for r, g, b in pixels]
    spread = statistics.pstdev(lum) if lum else 0
    mid = 80 < avg[0] < 180 and 80 < avg[1] < 180 and 80 < avg[2] < 180
    if mid and spread > 45:
        raise RuntimeError(
            f"export looks like IDE chrome (avg RGB={avg}, lum_std={spread:.1f}); "
            "PowerPoint window capture likely failed"
        )

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
