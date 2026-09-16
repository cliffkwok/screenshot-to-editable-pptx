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
    """pt from measured ink height. Latin uses cap-height ≈ 0.72em; CJK ≈ 0.88em."""
    ratio = 0.72 if script == "latin" else 0.88
    if glyph_h_px <= 0 or img_h <= 0:
        return 0.0
    return round(float(glyph_h_px) / float(img_h) * float(slide_h_in) * 72.0 / ratio, 1)


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
