#!/usr/bin/env python3
"""Measure every text line on a screenshot: ink box, glyph height, font pt.

Uses Tesseract for line strings when installed; always tightens boxes to ink
pixels so font size is not guessed. Same-level lines share one size_group.

Usage:
  python3 text_hints.py --image shot.png --out work/text_hints.json \\
      --overlay work/text_hints.png --slide-h 7.5 --lang eng+chi_tra
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mapping import font_pt_from_glyph, iou_xywh, refine_ink_box  # noqa: E402

_ALNUM = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]")


def _parse_tsv(stdout: str) -> list[dict]:
    lines = stdout.splitlines()
    if len(lines) < 2:
        return []
    header = lines[0].split("\t")
    idx = {name: i for i, name in enumerate(header)}
    words = []
    for row in lines[1:]:
        cols = row.split("\t")
        if len(cols) < len(header):
            continue
        try:
            level = int(cols[idx["level"]])
            conf = float(cols[idx["conf"]])
        except (KeyError, ValueError):
            continue
        if level != 5 or conf < 30:
            continue
        text = cols[idx.get("text", len(cols) - 1)].strip()
        if not text or not _ALNUM.search(text):
            continue
        w = int(cols[idx["width"]])
        h = int(cols[idx["height"]])
        if w < 2 or h < 5:
            continue
        words.append({
            "left": int(cols[idx["left"]]),
            "top": int(cols[idx["top"]]),
            "width": w,
            "height": h,
            "conf": conf,
            "text": text,
        })
    return words


def tesseract_words(image: Path, lang: str, psm: int) -> list[dict]:
    exe = shutil.which("tesseract")
    if not exe:
        return []
    cmd = [exe, str(image), "stdout", "-l", lang, "--psm", str(psm), "tsv"]
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not r.stdout.strip():
        return []
    return _parse_tsv(r.stdout)


def collect_full_image_words(image: Path, lang: str) -> list[dict]:
    trials = [lang]
    for part in lang.split("+"):
        if part and part not in trials:
            trials.append(part)
    if "eng" not in trials:
        trials.append("eng")
    words = []
    for lg in trials:
        for psm in (4, 6, 11, 3):
            words.extend(tesseract_words(image, lg, psm))
    return words


def find_colored_bars(im: Image.Image):
    """Horizontal saturated bands (header bars), split on x-gaps."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    chroma_n = []
    for y in range(h):
        n = 0
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if max(r, g, b) - min(r, g, b) >= 40:
                n += 1
        chroma_n.append(n)
    thresh = max(6, (w / 2) * 0.06)
    bars = []
    y = 0
    while y < h:
        if chroma_n[y] < thresh:
            y += 1
            continue
        y0 = y
        while y < h and chroma_n[y] >= thresh:
            y += 1
        y1 = y
        bh = y1 - y0
        if bh < 8 or bh > h * 0.16:
            continue
        colorful = []
        for yy in range(y0, y1):
            for x in range(w):
                r, g, b = px[x, yy]
                if max(r, g, b) - min(r, g, b) >= 40:
                    colorful.append(x)
        if len(colorful) < 40:
            continue
        colorful.sort()
        runs = []
        rs = colorful[0]
        prev = colorful[0]
        for x in colorful[1:]:
            if x - prev > 12:
                runs.append((rs, prev))
                rs = x
            prev = x
        runs.append((rs, prev))
        for x0, x1 in runs:
            bw = x1 - x0 + 1
            if bw < 24 or bw / bh < 1.8:
                continue
            bars.append((max(0, x0 - 4), max(0, y0 - 2), min(w, x1 + 5), min(h, y1 + 3)))
    return bars


def header_bar_words(im: Image.Image, lang: str, tmp_dir: Path) -> list[dict]:
    from PIL import ImageOps

    words = []
    bars = find_colored_bars(im)
    if not bars:
        return words
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for i, (x0, y0, x1, y1) in enumerate(bars):
        crop = im.crop((x0, y0, x1, y1))
        variants = [crop, ImageOps.invert(crop.convert("L")).convert("RGB")]
        got = []
        for vi, var in enumerate(variants):
            scale = 3 if var.size[1] < 48 else 2
            big = var.resize((var.size[0] * scale, var.size[1] * scale), Image.Resampling.BICUBIC)
            path = tmp_dir / f"bar_{i}_{vi}.png"
            big.save(path)
            for psm in (7, 6):
                got = tesseract_words(path, "eng", psm)
                if got:
                    break
            if got:
                for w in got:
                    w["left"] = int(round(w["left"] / scale + x0))
                    w["top"] = int(round(w["top"] / scale + y0))
                    w["width"] = max(2, int(round(w["width"] / scale)))
                    w["height"] = max(5, int(round(w["height"] / scale)))
                    w["from_bar"] = True
                    words.append(w)
                break
    return words


def dedup_words(words: list[dict]) -> list[dict]:
    kept = []
    for w in sorted(words, key=lambda x: -x["conf"]):
        box = [w["left"], w["top"], w["width"], w["height"]]
        if any(iou_xywh(box, [k["left"], k["top"], k["width"], k["height"]]) > 0.55 for k in kept):
            continue
        kept.append(w)
    return kept


def cluster_words_to_lines(words: list[dict], y_tol=0.55, gap_mul=3.2) -> list[dict]:
    """Y-band first (so a later-left word cannot split a title), then split on x-gaps."""
    words = sorted(words, key=lambda w: (w["top"] + w["height"] / 2.0, w["left"]))
    bands: list[list[dict]] = []
    for w in words:
        cy = w["top"] + w["height"] / 2.0
        placed = False
        for band in bands:
            med_h = statistics.median(x["height"] for x in band)
            band_cy = statistics.median(x["top"] + x["height"] / 2.0 for x in band)
            if abs(cy - band_cy) <= y_tol * max(med_h, w["height"]):
                band.append(w)
                placed = True
                break
        if not placed:
            bands.append([w])

    def _line(ws):
        ws = sorted(ws, key=lambda w: w["left"])
        heights = [w["height"] for w in ws]
        med = statistics.median(heights)
        inliers = [w for w in ws if 0.55 * med <= w["height"] <= 1.35 * med] or ws
        x = min(w["left"] for w in inliers)
        y = min(w["top"] for w in inliers)
        x2 = max(w["left"] + w["width"] for w in inliers)
        y2 = max(w["top"] + w["height"] for w in inliers)
        return {
            "box_px": [x, y, x2 - x, y2 - y],
            "text": " ".join(w["text"] for w in ws),
            "conf": sum(w["conf"] for w in ws) / len(ws),
            "word_heights": [w["height"] for w in inliers],
            "inlier_boxes": [[w["left"], w["top"], w["width"], w["height"]] for w in inliers],
            "backend": "tesseract",
        }

    lines = []
    for band in bands:
        band.sort(key=lambda w: w["left"])
        current = [band[0]]
        for w in band[1:]:
            last = current[-1]
            med_h = statistics.median(x["height"] for x in current)
            gap = w["left"] - (last["left"] + last["width"])
            if gap <= gap_mul * max(med_h, w["height"], 8):
                current.append(w)
            else:
                lines.append(_line(current))
                current = [w]
        lines.append(_line(current))
    lines.sort(key=lambda L: (L["box_px"][1], L["box_px"][0]))
    return lines


def line_glyph_height(im: Image.Image, raw: dict, refined) -> int:
    """Inlier-min ink height ≈ Latin cap-height; ignores circle-inflated OCR boxes."""
    heights = []
    for box in raw.get("inlier_boxes") or []:
        ink = refine_ink_box(im, box, extra_pad=1)
        heights.append(ink[1] if ink is not None else box[3])
    if not heights and raw.get("word_heights"):
        heights.extend(raw["word_heights"])
    if refined is not None:
        heights.append(refined[1])
    if not heights:
        return raw["box_px"][3]
    med = statistics.median(heights)
    kept = [h for h in heights if 0.55 * med <= h <= 1.35 * med] or heights
    return int(round(min(kept)))


def assign_size_groups(lines: list[dict], rel_tol=0.14):
    ordered = sorted(lines, key=lambda L: -L["glyph_height_px"])
    groups: list[list[dict]] = []
    for line in ordered:
        h = line["glyph_height_px"]
        placed = False
        for g in groups:
            med = statistics.median(x["glyph_height_px"] for x in g)
            if med > 0 and abs(h - med) / med <= rel_tol:
                g.append(line)
                placed = True
                break
        if not placed:
            groups.append([line])
    groups.sort(key=lambda g: -statistics.median(x["glyph_height_px"] for x in g))
    for i, g in enumerate(groups):
        latin = statistics.median(x["font_pt_if_latin"] for x in g)
        cjk = statistics.median(x["font_pt_if_cjk"] for x in g)
        for line in g:
            line["size_group"] = i
            line["size_group_font_pt_latin"] = round(latin, 1)
            line["size_group_font_pt_cjk"] = round(cjk, 1)
    return groups


def looks_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def measure(image: Path, slide_h=7.5, lang="eng+chi_tra") -> dict:
    im = Image.open(image).convert("RGB")
    img_w, img_h = im.size
    tmp = image.parent / ".text_hints_ocr"
    try:
        words = dedup_words(collect_full_image_words(image, lang) + header_bar_words(im, lang, tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    raw_lines = cluster_words_to_lines(words) if words else []
    # drop full-width junk near the bottom (rules / artifacts)
    cleaned = []
    for raw in raw_lines:
        x, y, w, h = raw["box_px"]
        if w > 0.85 * img_w and y > 0.82 * img_h:
            continue
        if w > 0.85 * img_w and h < 8:
            continue
        letters = len(_ALNUM.findall(raw["text"]))
        compact = re.sub(r"\s+", "", raw["text"])
        if letters < 3:
            continue
        if compact and letters / len(compact) < 0.35:
            continue
        cleaned.append(raw)
    # keep the higher-conf / longer string when two lines cover the same ink
    cleaned.sort(key=lambda L: (-L["conf"], -len(L["text"])))
    unique = []
    for raw in cleaned:
        if any(iou_xywh(raw["box_px"], u["box_px"]) > 0.45 for u in unique):
            continue
        unique.append(raw)
    unique.sort(key=lambda L: (L["box_px"][1], L["box_px"][0]))
    lines = []
    for i, raw in enumerate(unique):
        refined = refine_ink_box(im, raw["box_px"], extra_pad=2)
        gh = line_glyph_height(im, raw, refined)
        box = refined[0] if refined is not None else raw["box_px"]
        # if ink expand swallowed a diagram, keep the inlier word union
        if box[3] > gh * 1.8:
            box = raw["box_px"]
        script = "cjk" if looks_cjk(raw["text"]) else "latin"
        rec = {
            "id": f"L{i:03d}",
            "text": raw["text"],
            "box_px": box,
            "glyph_height_px": gh,
            "script": script,
            "font_pt_if_latin": font_pt_from_glyph(gh, img_h, slide_h, "latin"),
            "font_pt_if_cjk": font_pt_from_glyph(gh, img_h, slide_h, "cjk"),
            "conf": round(raw["conf"], 1),
            "backend": raw["backend"],
            "font_size_source": "measured",
        }
        lines.append(rec)
    assign_size_groups(lines)
    return {
        "image": str(image),
        "width_px": img_w,
        "height_px": img_h,
        "slide_h_in": slide_h,
        "line_count": len(lines),
        "size_groups": len({L["size_group"] for L in lines}) if lines else 0,
        "lines": lines,
    }


def draw_overlay(image: Path, data: dict, out: Path):
    im = Image.open(image).convert("RGB")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    for L in data["lines"]:
        x, y, w, h = L["box_px"]
        d.rectangle([x, y, x + w, y + h], outline=(255, 40, 0), width=2)
        label = f'{L["id"]} g{L["size_group"]} {L["size_group_font_pt_latin"]}pt'
        d.text((x, max(0, y - 12)), label, fill=(180, 0, 0), font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)


def main():
    p = argparse.ArgumentParser(description="Measure screenshot text lines (glyph boxes + pt)")
    p.add_argument("--image", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--overlay", default="")
    p.add_argument("--slide-h", type=float, default=7.5)
    p.add_argument("--lang", default="eng+chi_tra")
    args = p.parse_args()
    image = Path(args.image)
    if not image.exists():
        print(f"ERROR: image not found: {image}")
        sys.exit(1)
    data = measure(image, slide_h=args.slide_h, lang=args.lang)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.overlay:
        draw_overlay(image, data, Path(args.overlay))
    print(
        f"text_hints: {data['line_count']} lines, "
        f"{data['size_groups']} size groups → {out}"
    )
    if not data["lines"]:
        print("WARNING: no lines detected. Install tesseract or check the image.")
        sys.exit(1)


if __name__ == "__main__":
    main()
