#!/usr/bin/env python3
"""Audit spec boxes against the original screenshot — not spec vs XML.

verify_pptx checks the PPTX matches the spec. This checks the spec matches
the photo: each text box must contain ink, glyph height must match the
declared point size, and (when text_hints.json exists) the box must overlap
a measured line.

Usage:
  python3 source_audit.py --spec work/spec.json --original shot.png \\
      --hints work/text_hints.json --out work/source_audit.json
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mapping import (  # noqa: E402
    expected_glyph_h_px,
    ink_coverage,
    iou_xywh,
    pct_to_px,
    refine_ink_box,
)

GLYPH_RATIO_LO = 0.75
GLYPH_RATIO_HI = 1.35
INK_COVERAGE_MIN = 0.04
HINT_IOU_MIN = 0.15


def _script_for(el: dict) -> str:
    text = el.get("text") or ""
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "cjk"
    name = (el.get("font_name") or "").lower()
    if "pingfang" in name or "hei" in name or "song" in name or "kai" in name:
        return "cjk"
    return el.get("script") or "latin"


def _best_hint(box_px, hints: list[dict], text: str | None):
    scored = []
    needle = (text or "").strip().lower()
    for h in hints:
        iou = iou_xywh(box_px, h["box_px"])
        ht = (h.get("text") or "").strip().lower()
        bonus = 0.0
        if needle and ht:
            if needle == ht:
                bonus = 0.5
            elif needle in ht or ht in needle:
                bonus = 0.25
        scored.append((iou + bonus, iou, h))
    scored.sort(key=lambda t: -t[0])
    return scored[0] if scored else (0.0, 0.0, None)


def audit(spec: dict, original: Path, hints_data: dict | None):
    im = Image.open(original).convert("RGB")
    img_w, img_h = im.size
    slide = spec.get("slide") or {}
    slide_w = float(slide.get("width_in", 13.33))
    slide_h = float(slide.get("height_in", 7.5))
    fit = (spec.get("source") or {}).get("fit") or "height"
    src_w = (spec.get("source") or {}).get("width_px") or img_w
    src_h = (spec.get("source") or {}).get("height_px") or img_h
    hints = (hints_data or {}).get("lines") or []

    failures = []
    warnings = []
    checks = []

    for el in spec.get("elements") or []:
        kind = el.get("kind")
        name = el.get("name", "?")
        if kind not in ("text", "textbox") and not el.get("text"):
            continue
        if el.get("font_size_pt") is None:
            continue
        # Prefer explicit ink box (glyph measure). Container placement boxes
        # live in x_pct/… for verify and must not drive glyph-height audit.
        if el.get("box_px") and len(el["box_px"]) == 4:
            box_px = [int(round(v)) for v in el["box_px"]]
        else:
            try:
                box_px = pct_to_px(
                    el["x_pct"], el["y_pct"], el["w_pct"], el["h_pct"],
                    src_w, src_h, slide_w, slide_h, fit,
                )
            except KeyError:
                failures.append({
                    "element": name,
                    "code": "missing_box",
                    "message": "text element missing box_px and x_pct/y_pct/w_pct/h_pct",
                })
                continue
            box_px = [int(round(v)) for v in box_px]
        coverage, ink_h = ink_coverage(im, box_px)
        refined = refine_ink_box(im, box_px, extra_pad=2)
        glyph_h = refined[1] if refined else ink_h
        script = _script_for(el)
        expected = expected_glyph_h_px(el["font_size_pt"], src_h, slide_h, script)
        rec = {
            "element": name,
            "text": el.get("text"),
            "box_px": box_px,
            "ink_coverage": round(coverage, 4),
            "glyph_height_px": glyph_h,
            "expected_glyph_height_px": round(expected, 1),
            "font_size_pt": el["font_size_pt"],
            "font_size_source": el.get("font_size_source", "unspecified"),
            "script": script,
        }
        if coverage < INK_COVERAGE_MIN or glyph_h is None:
            rec["ok"] = False
            failures.append({
                "element": name,
                "code": "no_ink",
                "message": f"spec box has no ink on original (coverage={coverage:.3f})",
                "box_px": box_px,
            })
        else:
            ratio = glyph_h / expected if expected else 0
            rec["glyph_ratio"] = round(ratio, 3)
            host = el.get("host_box_px")
            inside_host = False
            if host and len(host) == 4:
                from mapping import ink_inside_shape
                inside_host = ink_inside_shape(box_px, host, pad_px=0)
                rec["inside_host"] = inside_host
                if not inside_host:
                    rec["ok"] = False
                    failures.append({
                        "element": name,
                        "code": "text_exceeds_shape",
                        "message": "text ink is not fully inside the host shape (visual: text must not overflow the fill)",
                        "box_px": box_px,
                        "host_box_px": host,
                    })
            # Shape-native labels: containment is the size gate; glyph-vs-pt
            # can disagree because pt is capped to the shape inner box.
            skip_glyph = (bool(host) and inside_host) or el.get("placement") == "container"
            if (not skip_glyph) and (ratio < GLYPH_RATIO_LO or ratio > GLYPH_RATIO_HI):
                rec["ok"] = False
                failures.append({
                    "element": name,
                    "code": "glyph_height",
                    "message": (
                        f"ink height {glyph_h}px vs {expected:.1f}px expected for "
                        f"{el['font_size_pt']}pt {script} (ratio {ratio:.2f})"
                    ),
                    "glyph_height_px": glyph_h,
                    "expected_glyph_height_px": round(expected, 1),
                })
            elif rec.get("ok") is not False:
                rec["ok"] = True
        if hints:
            score, iou, hint = _best_hint(box_px, hints, el.get("text"))
            rec["hint_id"] = hint["id"] if hint else None
            rec["hint_iou"] = round(iou, 3)
            rec["hint_text"] = hint.get("text") if hint else None
            if iou < HINT_IOU_MIN:
                rec["ok"] = False
                failures.append({
                    "element": name,
                    "code": "box_misses_line",
                    "message": (
                        f"spec box IoU {iou:.2f} vs measured line "
                        f"{hint['id'] if hint else '?'} {hint.get('text') if hint else ''}"
                    ),
                    "hint_iou": round(iou, 3),
                })
        if rec.get("font_size_source") in (None, "unspecified", "guessed"):
            warnings.append({
                "element": name,
                "code": "ungrounded_pt",
                "message": "font_size_source is not 'measured' — set from text_hints size_group",
            })
        checks.append(rec)

    passed = not failures
    return {
        "passed": passed,
        "original": str(original),
        "image_size": [img_w, img_h],
        "line_hints": len(hints),
        "checked": len(checks),
        "failures": failures,
        "warnings": warnings,
        "checks": checks,
    }


def main():
    p = argparse.ArgumentParser(description="Audit spec text boxes against the original screenshot")
    p.add_argument("--spec", required=True)
    p.add_argument("--original", required=True)
    p.add_argument("--hints", default="")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    spec_path = Path(args.spec)
    original = Path(args.original)
    if not spec_path.exists():
        print(f"ERROR: spec not found: {spec_path}")
        sys.exit(1)
    if not original.exists():
        print(f"ERROR: original not found: {original}")
        sys.exit(1)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    hints = None
    if args.hints:
        hp = Path(args.hints)
        if not hp.exists():
            print(f"ERROR: hints not found: {hp}")
            sys.exit(1)
        hints = json.loads(hp.read_text(encoding="utf-8"))

    report = audit(spec, original, hints)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 56)
    print("SOURCE AUDIT  (spec vs original screenshot)")
    print("=" * 56)
    print(f"  checked {report['checked']} text elements, {report['line_hints']} measured lines")
    mark = "PASSED" if report["passed"] else "FAILED"
    print(f"  OVERALL: {mark}  ({len(report['failures'])} failures, {len(report['warnings'])} warnings)")
    for f in report["failures"][:16]:
        print(f"          - {f['element']}: {f['message']}")
    extra = len(report["failures"]) - 16
    if extra > 0:
        print(f"          … {extra} more")
    print(f"Report: {out}")
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
