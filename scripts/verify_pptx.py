#!/usr/bin/env python3
"""Three-gate verifier: shape, font, color.

Exit 0 only when all three gates pass. The agent must not deliver the PPTX otherwise.

Usage:
  python3 verify_pptx.py \
    --pptx out.pptx \
    --spec spec.json \
    --original screenshot.png \
    --out verify_report.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

# Allow importing pptx_inspect from the same folder
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pptx_inspect import inspect_pptx  # noqa: E402

try:
    from PIL import Image
except ImportError:
    Image = None

COLOR_TOL = 2          # max channel delta
FONT_PT_TOL = 1.0      # points
POS_PCT_TOL = 3.0      # percent of slide
SIZE_PCT_TOL = 3.0

SHAPE_ALIASES = {
    "rounded_rectangle": "ROUNDED_RECTANGLE",
    "roundrect": "ROUNDED_RECTANGLE",
    "rounded rect": "ROUNDED_RECTANGLE",
    "pill": "ROUNDED_RECTANGLE",
    "rectangle": "RECTANGLE",
    "rect": "RECTANGLE",
    "oval": "OVAL",
    "circle": "OVAL",
    "ellipse": "OVAL",
    "triangle": "ISOSCELES_TRIANGLE",
    "isosceles_triangle": "ISOSCELES_TRIANGLE",
    "textbox": "TEXT_BOX",
    "text": "TEXT_BOX",
    "line": "RECTANGLE",
}


def parse_hex(h: str | None):
    if not h:
        return None
    h = h.lstrip("#").strip()
    if len(h) != 6:
        return None
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def color_delta(a, b) -> int | None:
    pa, pb = parse_hex(a), parse_hex(b)
    if pa is None or pb is None:
        return None
    return max(abs(pa[i] - pb[i]) for i in range(3))


def norm_shape(name: str | None) -> str | None:
    if not name:
        return None
    key = name.strip().lower().replace("-", "_").replace(" ", "_")
    return SHAPE_ALIASES.get(key, name.strip().upper())


def fail(gate, item, message, **extra):
    rec = {"element": item, "message": message}
    rec.update(extra)
    gate["failures"].append(rec)
    gate["passed"] = False


def sample_original(image_path: Path, xy):
    if Image is None:
        return None, "Pillow not installed"
    img = Image.open(image_path).convert("RGB")
    x, y = int(xy[0]), int(xy[1])
    w, h = img.size
    if not (0 <= x < w and 0 <= y < h):
        return None, f"coord ({x},{y}) outside {w}x{h}"
    r, g, b = img.getpixel((x, y))[:3]
    return f"#{r:02X}{g:02X}{b:02X}", None


def flatten_text_shapes(inspected):
    texts = []
    for s in inspected["shapes"]:
        font = s.get("font") or {}
        text = (font.get("text") or "").strip()
        if text:
            texts.append(s)
    return texts


def find_by_text(inspected, needle: str):
    needle = (needle or "").strip()
    if not needle:
        return None
    needle_one = " ".join(needle.split())
    contained = None
    for s in flatten_text_shapes(inspected):
        got = (s["font"]["text"] or "").strip()
        got_one = " ".join(got.split())
        if got == needle or got_one == needle_one:
            return s
        if needle_one in got_one and (contained is None or len(got_one) < len(contained["font"]["text"])):
            contained = s
    return contained


def find_by_name_or_pos(inspected, el):
    name = el.get("name")
    for s in inspected["shapes"]:
        if name and s.get("name") == name:
            return s
    # nearest same-type shape by position
    want_type = norm_shape(el.get("shape_type"))
    wx, wy = el.get("x_pct"), el.get("y_pct")
    if wx is None or wy is None:
        return None
    best, best_d = None, 1e9
    for s in inspected["shapes"]:
        if s.get("kind") == "group":
            continue
        st = s.get("shape_type")
        if want_type == "TEXT_BOX":
            if s.get("kind") != "textbox" and not (s.get("font") or {}).get("text"):
                continue
        elif want_type and st and st != want_type:
            continue
        d = math.hypot((s.get("x_pct") or 0) - wx, (s.get("y_pct") or 0) - wy)
        if d < best_d:
            best, best_d = s, d
    if best_d > POS_PCT_TOL * 3:
        return None
    return best


def first_run(shape_rec):
    font = shape_rec.get("font") or {}
    runs = font.get("runs") or []
    return runs[0] if runs else {}


def find_filled_sibling(inspected, seed, expected_hex=None):
    """When a fill probe hits a text box, use a filled shape in the same group/area."""
    if seed and seed.get("fill") and (
        expected_hex is None or (color_delta(expected_hex, seed.get("fill")) or 999) <= COLOR_TOL
    ):
        return seed
    path = (seed or {}).get("group_path")
    sx, sy = (seed or {}).get("x_pct") or 0, (seed or {}).get("y_pct") or 0
    candidates = []
    for s in inspected["shapes"]:
        if not s.get("fill") or s.get("kind") == "group":
            continue
        if path and s.get("group_path") != path:
            continue
        d = math.hypot((s.get("x_pct") or 0) - sx, (s.get("y_pct") or 0) - sy)
        delta = color_delta(expected_hex, s.get("fill")) if expected_hex else 0
        candidates.append((delta if delta is not None else 999, d, s))
    if expected_hex:
        color_hits = [c for c in candidates if c[0] <= COLOR_TOL]
        if color_hits:
            color_hits.sort(key=lambda c: c[1])
            return color_hits[0][2]
        # any slide shape with this fill
        for s in inspected["shapes"]:
            dlt = color_delta(expected_hex, s.get("fill"))
            if dlt is not None and dlt <= COLOR_TOL:
                return s
    if not candidates:
        return seed if seed and seed.get("fill") else None
    candidates.sort(key=lambda c: c[1])
    return candidates[0][2]


def resolve_probe_target(inspected, probe):
    apply_on = probe.get("apply", "fill")
    expected = probe.get("hex")
    target = None
    if probe.get("element"):
        dummy = {
            "name": probe["element"],
            "shape_type": probe.get("shape_type"),
            "x_pct": probe.get("x_pct"),
            "y_pct": probe.get("y_pct"),
        }
        target = find_by_name_or_pos(inspected, dummy)
    if target is None and probe.get("text"):
        target = find_by_text(inspected, probe["text"])
    if apply_on == "fill":
        target = find_filled_sibling(inspected, target, expected)
        if target is None:
            dummy = {
                "name": probe.get("name"),
                "shape_type": probe.get("shape_type"),
                "x_pct": probe.get("x_pct"),
                "y_pct": probe.get("y_pct"),
            }
            target = find_by_name_or_pos(inspected, dummy)
            target = find_filled_sibling(inspected, target, expected)
    return target, apply_on


def check_color(spec, inspected, original: Path | None, gate):
    probes = spec.get("color_probes") or []
    if not probes:
        fail(gate, "spec", "spec.json is missing color_probes — fail closed")
        return

    bg = spec.get("slide", {}).get("background")
    if bg:
        actual = (inspected.get("slide") or {}).get("background")
        if actual:
            d = color_delta(bg, actual)
            if d is not None and d > COLOR_TOL:
                fail(gate, "slide.background", "background hex mismatch",
                     expected=bg, actual=actual, delta=d)

    for probe in probes:
        name = probe.get("name", "unnamed")
        expected = probe.get("hex")
        if not expected:
            fail(gate, name, "color probe missing hex")
            continue

        if original and probe.get("px"):
            sampled, err = sample_original(original, probe["px"])
            if err:
                fail(gate, name, f"cannot re-sample original: {err}", px=probe["px"])
            else:
                d = color_delta(expected, sampled)
                if d is not None and d > COLOR_TOL:
                    fail(gate, name,
                         "spec hex does not match original screenshot (guessed color?)",
                         expected=expected, sampled_from_original=sampled,
                         delta=d, px=probe["px"])

        target, apply_on = resolve_probe_target(inspected, probe)
        if target is None:
            fills = [s.get("fill") for s in inspected["shapes"] if s.get("fill")]
            ok = any(
                color_delta(expected, f) is not None and color_delta(expected, f) <= COLOR_TOL
                for f in fills
            )
            if not ok:
                fail(gate, name, "expected hex not found on any PPT shape fill",
                     expected=expected)
            continue

        if apply_on == "font":
            run = first_run(target)
            actual = run.get("color")
        else:
            actual = target.get("fill")
        d = color_delta(expected, actual)
        if actual is None:
            fail(gate, name, f"PPT {apply_on} color missing (theme color? use RGBColor)",
                 expected=expected)
        elif d is not None and d > COLOR_TOL:
            fail(gate, name, f"PPT {apply_on} hex mismatch",
                 expected=expected, actual=actual, delta=d)


def check_font(spec, inspected, gate):
    elements = [e for e in spec.get("elements", []) if e.get("kind") in ("text", "textbox") or e.get("text")]
    if not elements:
        fail(gate, "spec", "spec.json has no text elements — fail closed")
        return

    for el in elements:
        name = el.get("name", el.get("text", "text")[:40])
        want_text = el.get("text")
        target = find_by_text(inspected, want_text) if want_text else find_by_name_or_pos(inspected, el)
        if target is None:
            fail(gate, name, "text not found in PPTX", expected_text=want_text)
            continue
        run = first_run(target)
        got_text = (target.get("font") or {}).get("text", "").strip()
        if want_text and want_text.strip() not in got_text and got_text not in want_text.strip():
            fail(gate, name, "text content mismatch", expected=want_text, actual=got_text)

        if el.get("font_name"):
            got_name = run.get("font_name")
            if got_name and got_name.lower() != el["font_name"].lower():
                fail(gate, name, "font name mismatch",
                     expected=el["font_name"], actual=got_name)
            elif not got_name:
                fail(gate, name, "PPT run has no font name", expected=el["font_name"])

        if el.get("font_size_pt") is not None:
            got_sz = run.get("font_size_pt")
            if got_sz is None:
                fail(gate, name, "PPT run has no font size", expected=el["font_size_pt"])
            elif abs(got_sz - float(el["font_size_pt"])) > FONT_PT_TOL:
                fail(gate, name, "font size mismatch",
                     expected=el["font_size_pt"], actual=got_sz)

        if "bold" in el:
            got_bold = bool(run.get("bold"))
            if got_bold != bool(el["bold"]):
                fail(gate, name, "bold mismatch", expected=el["bold"], actual=got_bold)

        if el.get("color"):
            d = color_delta(el["color"], run.get("color"))
            if run.get("color") is None:
                fail(gate, name, "text color missing on PPT run", expected=el["color"])
            elif d is not None and d > COLOR_TOL:
                fail(gate, name, "text color mismatch",
                     expected=el["color"], actual=run.get("color"), delta=d)


def radius_class(val, shape_type):
    if norm_shape(shape_type) == "ROUNDED_RECTANGLE" or shape_type == "pill":
        if val is None:
            return "unknown"
        if val >= 0.45:
            return "pill"
        if val >= 0.12:
            return "large"
        return "small"
    return None


def check_shape(spec, inspected, gate):
    elements = spec.get("elements") or []
    if not elements:
        fail(gate, "spec", "spec.json has no elements — fail closed")
        return

    allow_pictures = bool(spec.get("allow_pictures"))
    if inspected.get("pictures", 0) > 0 and not allow_pictures:
        fail(gate, "pictures",
             "PPT contains raster pictures; screenshot reconstruction must be native shapes",
             count=inspected["pictures"])

    groups_required = spec.get("groups_required", True)
    if groups_required and inspected.get("groups", 0) < 1:
        fail(gate, "groups", "no grouped shapes — output is not scalable")

    for s in inspected.get("shapes") or []:
        if s.get("kind") != "group":
            continue
        if s.get("coord_mode") == "DOUBLE_OFFSET_BUG":
            fail(
                gate,
                s.get("name") or "group",
                "group xfrm is double-offset (chOff non-zero but children already local). "
                "PowerPoint will park this group at the slide origin even if python-pptx .left looks correct.",
                chOff_emu=s.get("chOff_emu"),
            )

    slide_spec = spec.get("slide") or {}
    if slide_spec.get("width_in"):
        actual_w = inspected["slide"]["width_in"]
        if abs(actual_w - float(slide_spec["width_in"])) > 0.05:
            fail(gate, "slide", "slide width mismatch",
                 expected=slide_spec["width_in"], actual=actual_w)
    if slide_spec.get("height_in"):
        actual_h = inspected["slide"]["height_in"]
        if abs(actual_h - float(slide_spec["height_in"])) > 0.05:
            fail(gate, "slide", "slide height mismatch",
                 expected=slide_spec["height_in"], actual=actual_h)

    used = set()
    for el in elements:
        name = el.get("name", "unnamed")
        want_type = norm_shape(el.get("shape_type") or el.get("kind"))
        target = None
        if el.get("text"):
            target = find_by_text(inspected, el["text"])
        if target is None:
            target = find_by_name_or_pos(inspected, el)
        if target is None:
            fail(gate, name, "shape not found in PPTX",
                 expected_type=want_type, expected_text=el.get("text"))
            continue
        used.add(id(target))

        got_type = target.get("shape_type")
        got_kind = target.get("kind")
        if want_type == "TEXT_BOX":
            if got_kind not in ("textbox", "shape") and not (target.get("font") or {}).get("text"):
                fail(gate, name, "expected text box", actual_kind=got_kind)
        elif want_type and got_type and got_type != want_type:
            fail(gate, name, "shape type mismatch",
                 expected=want_type, actual=got_type)

        if el.get("shape_type") == "circle" or el.get("is_circle"):
            if not target.get("is_circle", False) and got_type == "OVAL":
                fail(gate, name, "circle constraint failed (width != height)",
                     w_pct=target.get("w_pct"), h_pct=target.get("h_pct"))

        if el.get("shape_type") == "pill" or el.get("radius") == 0.5:
            r = target.get("radius")
            if r is None or r < 0.45:
                fail(gate, name, "expected pill (radius ~= 0.5)", actual_radius=r)

        if el.get("radius") is not None and target.get("radius") is not None:
            if abs(float(el["radius"]) - float(target["radius"])) > 0.08:
                fail(gate, name, "corner radius mismatch",
                     expected=el["radius"], actual=target["radius"])

        for axis, tol in (("x_pct", POS_PCT_TOL), ("y_pct", POS_PCT_TOL),
                          ("w_pct", SIZE_PCT_TOL), ("h_pct", SIZE_PCT_TOL)):
            if el.get(axis) is None:
                continue
            actual = target.get(axis)
            if actual is None:
                continue
            if abs(float(el[axis]) - float(actual)) > tol:
                fail(gate, name, f"{axis} outside ±{tol}%",
                     expected=el[axis], actual=actual)

        if "has_shadow" in el:
            if bool(el["has_shadow"]) != bool(target.get("has_shadow")):
                fail(gate, name, "shadow mismatch",
                     expected=el["has_shadow"], actual=target.get("has_shadow"))


def verify(pptx: Path, spec: dict, original: Path | None, slide_index: int):
    inspected = inspect_pptx(pptx, slide_index)
    gates = {
        "shape": {"passed": True, "failures": []},
        "font": {"passed": True, "failures": []},
        "color": {"passed": True, "failures": []},
    }
    check_shape(spec, inspected, gates["shape"])
    check_font(spec, inspected, gates["font"])
    check_color(spec, inspected, original, gates["color"])
    passed = all(g["passed"] for g in gates.values())
    return {
        "passed": passed,
        "gates": gates,
        "pptx": str(pptx),
        "original": str(original) if original else None,
        "inspect_summary": {
            "shape_count": len(inspected["shapes"]),
            "groups": inspected["groups"],
            "pictures": inspected["pictures"],
            "slide": inspected["slide"],
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Verify PPTX shape, font, and color against spec")
    parser.add_argument("--pptx", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--original", default="", help="Original screenshot PNG (required for color re-sample)")
    parser.add_argument("--slide", type=int, default=0)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    pptx = Path(args.pptx)
    spec_path = Path(args.spec)
    if not pptx.exists():
        print(f"ERROR: PPTX not found: {pptx}")
        sys.exit(1)
    if not spec_path.exists():
        print(f"ERROR: spec not found: {spec_path}")
        sys.exit(1)

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    original = Path(args.original) if args.original else None
    if original and not original.exists():
        print(f"ERROR: original screenshot not found: {original}")
        sys.exit(1)
    if not original:
        print("WARNING: --original omitted; color gate cannot re-sample the screenshot.")

    report = verify(pptx, spec, original, args.slide)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 56)
    print("SHAPE / FONT / COLOR VERIFICATION")
    print("=" * 56)
    for name, gate in report["gates"].items():
        mark = "PASS" if gate["passed"] else "FAIL"
        print(f"  {name.upper():6}  {mark}  ({len(gate['failures'])} issues)")
        for f in gate["failures"][:12]:
            print(f"          - {f['element']}: {f['message']}")
        extra = len(gate["failures"]) - 12
        if extra > 0:
            print(f"          … {extra} more")
    print("-" * 56)
    print("OVERALL:", "PASSED" if report["passed"] else "FAILED")
    print(f"Report: {out}")

    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
