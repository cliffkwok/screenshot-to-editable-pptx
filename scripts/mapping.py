"""Map screenshot pixels ↔ slide inches. Shared by text_hints, source_audit, builders."""
from __future__ import annotations

from pptx.util import Inches

try:
    from PIL import Image
except ImportError:
    Image = None


def screenshot_mapping(img_w, img_h, slide_w=13.33, slide_h=7.5, fit="height"):
    """Return (scale_in_per_px, ox_in, oy_in)."""
    img_w, img_h = float(img_w), float(img_h)
    slide_w, slide_h = float(slide_w), float(slide_h)
    if fit == "width":
        scale = slide_w / img_w
        return scale, 0.0, (slide_h - img_h * scale) / 2.0
    if fit == "stretch":
        return None, 0.0, 0.0
    scale = slide_h / img_h
    return scale, (slide_w - img_w * scale) / 2.0, 0.0


def px_box_to_inches(x, y, w, h, img_w, img_h, slide_w=13.33, slide_h=7.5, fit="height"):
    scale, ox, oy = screenshot_mapping(img_w, img_h, slide_w, slide_h, fit)
    if scale is None:
        return (
            Inches(x / img_w * slide_w),
            Inches(y / img_h * slide_h),
            Inches(w / img_w * slide_w),
            Inches(h / img_h * slide_h),
        )
    return (
        Inches(ox + x * scale),
        Inches(oy + y * scale),
        Inches(w * scale),
        Inches(h * scale),
    )


def pct_to_px(x_pct, y_pct, w_pct, h_pct, img_w, img_h, slide_w=13.33, slide_h=7.5, fit="height"):
    scale, ox, oy = screenshot_mapping(img_w, img_h, slide_w, slide_h, fit)
    if scale is None:
        return (
            x_pct / 100.0 * img_w,
            y_pct / 100.0 * img_h,
            w_pct / 100.0 * img_w,
            h_pct / 100.0 * img_h,
        )
    l = x_pct / 100.0 * slide_w
    t = y_pct / 100.0 * slide_h
    ww = w_pct / 100.0 * slide_w
    hh = h_pct / 100.0 * slide_h
    return (
        (l - ox) / scale,
        (t - oy) / scale,
        ww / scale,
        hh / scale,
    )


def font_pt_from_glyph(glyph_h_px, img_h, slide_h_in=7.5, script="latin"):
    """pt from measured **cap-height** (not full-string bbox with descenders).

    Latin uses cap-height ≈ 0.72em; CJK ≈ 0.88em.
    Pass height of a capital / first-line caps only — including `g`/`y` descenders
    inflates pt and collapses neighboring text gaps in PPT.
    """
    ratio = 0.72 if script == "latin" else 0.88
    if glyph_h_px <= 0 or img_h <= 0:
        return 0.0
    return round(float(glyph_h_px) / float(img_h) * float(slide_h_in) * 72.0 / ratio, 1)


def font_pt_from_cap_height(cap_h_px, img_h, slide_h_in=7.5, script="latin"):
    """Alias — prefer this name at call sites so agents do not pass descender bboxes."""
    return font_pt_from_glyph(cap_h_px, img_h, slide_h_in, script)


def one_line_box_width(
    text: str,
    size_pt: float,
    ink_w_px: int,
    *,
    img_w: int,
    img_h: int,
    slide_w: float = 13.33,
    slide_h: float = 7.5,
    char_em: float = 0.55,
    slack_px: int = 12,
    max_right_px: int | None = None,
    left_px: int = 0,
) -> int:
    """Widen a one-line text box so PPT glyphs (approx) fit without wrap.

    Photo UI fonts are often narrower than Arial. Ink width alone can force
    wrap=True disasters — keep wrap=False and return a safer pixel width.
    """
    scale, _, _ = screenshot_mapping(img_w, img_h, slide_w, slide_h, "height")
    # approx string width in inches → px
    approx_in = max(1, len(text or "")) * (float(size_pt) / 72.0) * float(char_em)
    need_px = int(approx_in / scale) + int(slack_px) if scale else ink_w_px
    width = max(int(ink_w_px), need_px)
    if max_right_px is not None:
        width = min(width, int(max_right_px) - int(left_px))
    return max(1, width)


def font_pt_fit_shape(
    text,
    shape_w_in,
    shape_h_in,
    glyph_pt=None,
    script="latin",
    pad_frac=None,
    margin_pt=3.0,
    circle=False,
):
    """Cap pt so the string stays *inside* the host shape (visual rule).

    PowerPoint's line box is ~1em tall, not cap-height. Text on a bar/circle
    must leave padding; circles clip more, so they get a tighter usable box.

    `pad_frac` is the fraction of shape width/height kept empty on *each* side
    (0.25 → text uses the middle 50%). Prefer a value **measured** from the
    screenshot (ink vs fill). Defaults: bar ~0.12, circle ~0.22.
    Glyph-measured pt is an upper bound — never larger than the shape allows.
    """
    text = text or ""
    w = max(1e-6, float(shape_w_in))
    h = max(1e-6, float(shape_h_in))
    m = float(margin_pt) / 72.0
    inner_w = max(1e-6, w - 2 * m)
    inner_h = max(1e-6, h - 2 * m)
    if pad_frac is None:
        pad = 0.22 if circle else 0.12
    else:
        pad = max(0.0, float(pad_frac))
    inner_w *= (1 - 2 * pad)
    inner_h *= (1 - 2 * pad)
    # line-box height ≈ 1.05em in PPT
    max_from_h = inner_h / 1.05 * 72.0
    avg_em = 1.02 if script == "cjk" else (0.55 if circle else 0.54)
    letters = max(1.0, sum(0.33 if ch == " " else 1.0 for ch in text) or 1.0)
    max_from_w = inner_w / (letters * avg_em) * 72.0
    cap = min(max_from_h, max_from_w)
    cap = max(5.0, cap)
    if glyph_pt is None:
        return round(cap, 1)
    return round(min(float(glyph_pt), cap), 1)


def measure_text_in_shape(im, box_px, circle=False):
    """Measure ink-vs-fill gap inside a host shape on the screenshot.

    Returns dict with pad_l/r/t/b (px), pad_frac (min horizontal side / width),
    pad_frac_y, ink_w/h, ink_w_frac/ink_h_frac, glyph_pt (latin from ink height).
    Detects label ink as pixels clearly brighter than the fill median — not the
    fill itself (JPEG anti-alias can look “bright” without being text).
    """
    if Image is None:
        raise RuntimeError("Pillow is required")
    x, y, w, h = [int(round(v)) for v in box_px]
    rgb = im.convert("RGB") if im.mode != "RGB" else im
    px = rgb.load()
    W, H = rgb.size
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + max(1, w)), min(H, y + max(1, h))
    cx = (x0 + x1 - 1) / 2.0
    cy = (y0 + y1 - 1) / 2.0
    diam = max(x1 - x0, y1 - y0)
    r_lim = diam * (0.45 if circle else 0.70)

    samples = []
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            if circle and ((yy - cy) ** 2 + (xx - cx) ** 2) ** 0.5 > r_lim:
                continue
            r, g, b = px[xx, yy]
            lum = (r + g + b) / 3.0
            samples.append((lum, r, g, b, xx, yy))
    if len(samples) < 20:
        return None
    lums = sorted(s[0] for s in samples)
    med = lums[len(lums) // 2]
    p90 = lums[int(len(lums) * 0.90)]
    # Text must outshine fill; require a real gap so anti-aliased fill edge
    # does not count as the whole disk being "ink".
    thresh = max(med + 35.0, (med + p90) / 2.0)
    ink = [(s[4], s[5]) for s in samples if s[0] >= thresh]
    # Near-white always counts (classic white-on-color labels)
    for lum, r, g, b, xx, yy in samples:
        if min(r, g, b) >= 200 and max(r, g, b) - min(r, g, b) < 55:
            ink.append((xx, yy))
    ink = list(set(ink))
    if len(ink) < 5:
        return None
    # Reject "ink" that covers most of the shape — that is fill, not a label
    xs = [p[0] for p in ink]
    ys = [p[1] for p in ink]
    iw = max(xs) - min(xs) + 1
    ih = max(ys) - min(ys) + 1
    bw = max(1, x1 - x0)
    bh = max(1, y1 - y0)
    if iw / bw > 0.85 or ih / bh > 0.85:
        # Too large: keep only the brightest core
        core_cut = lums[int(len(lums) * 0.96)]
        ink = [(s[4], s[5]) for s in samples if s[0] >= core_cut]
        if len(ink) < 5:
            return None
        xs = [p[0] for p in ink]
        ys = [p[1] for p in ink]
        iw = max(xs) - min(xs) + 1
        ih = max(ys) - min(ys) + 1
        if iw / bw > 0.85 or ih / bh > 0.85:
            return None

    pad_l = min(xs) - x0
    pad_r = (x1 - 1) - max(xs)
    pad_t = min(ys) - y0
    pad_b = (y1 - 1) - max(ys)
    pad_frac = max(0.0, min(pad_l, pad_r) / bw)
    pad_frac_y = max(0.0, min(pad_t, pad_b) / bh)
    pad_use = max(pad_frac, pad_frac_y * 0.85)
    glyph_pt = round(ih / H * 7.5 * 72.0 / 0.72, 1)
    return {
        "box_px": (x0, y0, bw, bh),
        "ink_box_px": (min(xs), min(ys), iw, ih),
        "pad_l": pad_l,
        "pad_r": pad_r,
        "pad_t": pad_t,
        "pad_b": pad_b,
        "pad_frac": round(pad_use, 3),
        "pad_frac_x": round(pad_frac, 3),
        "pad_frac_y": round(pad_frac_y, 3),
        "ink_w": iw,
        "ink_h": ih,
        "ink_w_frac": round(iw / bw, 3),
        "ink_h_frac": round(ih / bh, 3),
        "glyph_pt": glyph_pt,
    }


def ink_inside_shape(ink_box, shape_box, pad_px=2):
    """True if ink rectangle is fully inside the shape with a small pad."""
    ix, iy, iw, ih = [float(v) for v in ink_box]
    sx, sy, sw, sh = [float(v) for v in shape_box]
    return (
        ix >= sx + pad_px
        and iy >= sy + pad_px
        and ix + iw <= sx + sw - pad_px
        and iy + ih <= sy + sh - pad_px
    )


def expected_glyph_h_px(font_pt, img_h, slide_h_in=7.5, script="latin"):
    ratio = 0.72 if script == "latin" else 0.88
    return float(font_pt) / 72.0 * (float(img_h) / float(slide_h_in)) * ratio


def pad_ink_box_px(x, y, w, h, pad_x_ratio=0.14, pad_y_ratio=0.20, img_w=None, img_h=None):
    """Expand a tight glyph box so PPT does not clip or wrap."""
    px = max(2, int(round(h * pad_x_ratio)))
    py = max(2, int(round(h * pad_y_ratio)))
    nx, ny = x - px, y - py
    nw, nh = w + 2 * px, h + 2 * py
    if img_w is not None:
        nx = max(0, nx)
        nw = min(nw, img_w - nx)
    if img_h is not None:
        ny = max(0, ny)
        nh = min(nh, img_h - ny)
    return int(nx), int(ny), int(nw), int(nh)


def _border_bg(px, x0, y0, x1, y1):
    samples = []
    for x in range(x0, x1):
        samples.append(px[x, y0][:3])
        samples.append(px[x, y1 - 1][:3])
    for y in range(y0, y1):
        samples.append(px[x0, y][:3])
        samples.append(px[x1 - 1, y][:3])
    if not samples:
        return (255, 255, 255)
    rs = sorted(s[0] for s in samples)
    gs = sorted(s[1] for s in samples)
    bs = sorted(s[2] for s in samples)
    n = len(rs) // 2
    return (rs[n], gs[n], bs[n])


def refine_ink_box(im, box, contrast=38, extra_pad=3):
    """Tighten a pixel box to ink vs border-median background.

    Returns (box_px [x,y,w,h], glyph_height_px, ink_count) or None.
    """
    if Image is None:
        raise RuntimeError("Pillow is required")
    w, h = im.size
    x, y, bw, bh = [int(v) for v in box]
    x0, y0 = max(0, x - extra_pad), max(0, y - extra_pad)
    x1, y1 = min(w, x + bw + extra_pad), min(h, y + bh + extra_pad)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return None
    rgb = im.convert("RGB") if im.mode != "RGB" else im
    px = rgb.load()
    br, bg, bb = _border_bg(px, x0, y0, x1, y1)
    xs, ys = [], []
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            r, g, b = px[xx, yy]
            d = max(abs(r - br), abs(g - bg), abs(b - bb))
            if d >= contrast:
                xs.append(xx)
                ys.append(yy)
    if len(xs) < 8:
        return None
    ix, iy = min(xs), min(ys)
    iw, ih = max(xs) - ix + 1, max(ys) - iy + 1
    if iw < 3 or ih < 4:
        return None
    return [ix, iy, iw, ih], ih, len(xs)


def ink_coverage(im, box, contrast=38):
    refined = refine_ink_box(im, box, contrast=contrast, extra_pad=0)
    area = max(1, int(box[2]) * int(box[3]))
    if refined is None:
        return 0.0, None
    _, gh, count = refined
    return count / area, gh


def iou_xywh(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh
    ix0, iy0 = max(ax, bx), max(ay, by)
    ix1, iy1 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0
