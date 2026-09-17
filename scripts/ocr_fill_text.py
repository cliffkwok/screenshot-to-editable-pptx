#!/usr/bin/env python3
"""Optional OCR fill: attach Tesseract strings to measured Layer C boxes.

Does NOT invent positions or font pt — only fills `text` on existing boxes
(from layout / _layers / text_hints). Prefer measured glyph pt from text_hints.

Usage:
  python3 scripts/ocr_fill_text.py \\
      --image work/deck/original.png \\
      --layout work/deck/layout.json \\
      --out work/deck/layout_ocr.json \\
      --lang eng
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required")
    sys.exit(1)


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def ocr_crop(im: Image.Image, box, lang: str = "eng") -> str:
    x, y, w, h = [int(v) for v in box]
    crop = im.crop((x, y, x + w, y + h))
    # slight pad helps OCR
    pad = 4
    padded = Image.new("RGB", (crop.width + 2 * pad, crop.height + 2 * pad), (255, 255, 255))
    padded.paste(crop.convert("RGB"), (pad, pad))
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = Path(f.name)
        padded.save(path)
    try:
        r = subprocess.run(
            ["tesseract", str(path), "stdout", "-l", lang, "--psm", "6"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        text = (r.stdout or "").strip()
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        return text
    finally:
        path.unlink(missing_ok=True)


def fill_layout(layout: dict, image: Path, lang: str) -> dict:
    im = Image.open(image).convert("RGB")
    out = json.loads(json.dumps(layout))  # deep copy
    elements = out.get("elements") or []
    slides = out.get("slides")
    if slides:
        targets = []
        for s in slides:
            targets.extend(s.get("elements") or [])
    else:
        targets = elements

    filled = 0
    for el in targets:
        if el.get("type") not in ("text", "textbox", None) and el.get("layer") != "C":
            # only fill text-like
            if "text" not in el and el.get("type") not in ("text", "textbox"):
                continue
        if el.get("type") in ("image", "shape", "line", "picture"):
            continue
        box = el.get("box_px") or el.get("box")
        if not box or len(box) != 4:
            continue
        # skip if already has substantial text
        existing = (el.get("text") or "").strip()
        if len(existing) >= 2 and not el.get("ocr_refill"):
            continue
        try:
            got = ocr_crop(im, box, lang=lang)
        except Exception as e:
            el["ocr_error"] = str(e)
            continue
        if got:
            el["text"] = got
            el["text_source"] = "ocr"
            filled += 1
    out["_ocr"] = {"filled": filled, "lang": lang, "engine": "tesseract"}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", required=True)
    ap.add_argument("--layout", required=True, help="layout.json or _layers.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", default="eng")
    args = ap.parse_args()
    if not tesseract_available():
        print("ERROR: tesseract not on PATH — install it or skip OCR fill")
        sys.exit(2)
    layout = json.loads(Path(args.layout).read_text())
    out = fill_layout(layout, Path(args.image), args.lang)
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"wrote {args.out}  filled={out.get('_ocr', {}).get('filled')}")


if __name__ == "__main__":
    main()
