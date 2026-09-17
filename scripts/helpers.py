"""python-pptx helpers for screenshot reconstruction.

Import from a builder script after putting this folder on sys.path:

    from helpers import (
        new_presentation, add_shape, add_text, add_shadow,
        disable_shadow, group_shapes, rgb, inch_pct
    )
"""
from pathlib import Path
import sys

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR, MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mapping import (  # noqa: E402
    Image,
    expected_glyph_h_px,
    font_pt_fit_shape,
    font_pt_from_glyph,
    ink_inside_shape,
    measure_text_in_shape,
    pad_ink_box_px,
    pct_to_px,
    px_box_to_inches,
    screenshot_mapping,
)

ALIGN = {
    "left": PP_ALIGN.LEFT,
    "center": PP_ALIGN.CENTER,
    "right": PP_ALIGN.RIGHT,
}


def rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def new_presentation(width_in=13.33, height_in=7.5):
    prs = Presentation()
    prs.slide_width = Inches(width_in)
    prs.slide_height = Inches(height_in)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    return prs, slide


def set_background(slide, hex_color: str):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = rgb(hex_color)


def disable_shadow(shape):
    """Kill python-pptx default shadow. Call on every shape."""
    try:
        shape.shadow.inherit = False
    except Exception:
        pass
    return shape


def add_shape(slide, typ, l, t, w, h, fill=None, line=None, lw=None, rad=None):
    sh = slide.shapes.add_shape(typ, l, t, w, h)
    if fill:
        sh.fill.solid()
        sh.fill.fore_color.rgb = rgb(fill) if isinstance(fill, str) else fill
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = rgb(line) if isinstance(line, str) else line
        sh.line.width = lw or Pt(1)
    else:
        sh.line.fill.background()
    if rad is not None:
        sh.adjustments[0] = rad
    disable_shadow(sh)
    return sh


def set_shape_text(
    shape, text, size_pt, bold=False, color="#FFFFFF", font="Arial",
    align="center", anchor="middle", margin_pt=3, autofit=False, wrap=False,
    fit_to_shape=True, circle=False, pad_frac=None,
):
    """Put text *inside* a shape (PowerPoint: select shape → Edit Text).

    Prefer this over a separate text box when the screenshot shows a label
    on a filled bar/pill/circle. Point size is capped so the line box stays
    inside the shape with the same gap as the photo (`pad_frac` measured from
    ink vs fill). `autofit` is off by default so PPT does not fight the size.
    """
    pt = float(size_pt)
    if fit_to_shape:
        pt = font_pt_fit_shape(
            text,
            shape.width.inches,
            shape.height.inches,
            glyph_pt=pt,
            margin_pt=margin_pt,
            circle=circle,
            pad_frac=pad_frac,
        )
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = wrap
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE if autofit else MSO_AUTO_SIZE.NONE
    if anchor == "middle":
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    elif anchor == "bottom":
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
    else:
        tf.vertical_anchor = MSO_ANCHOR.TOP
    m = Pt(margin_pt)
    tf.margin_left = m
    tf.margin_right = m
    tf.margin_top = m
    tf.margin_bottom = m
    lines = str(text).split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if i == 0:
            p.clear()
        p.alignment = ALIGN.get(align, PP_ALIGN.CENTER)
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        run = p.add_run()
        run.text = line
        run.font.size = Pt(pt)
        run.font.bold = bold
        run.font.color.rgb = rgb(color) if isinstance(color, str) else color
        run.font.name = font
    shape._fit_font_pt = pt
    return shape


def add_shape_with_text(
    slide, typ, l, t, w, h, text, size_pt,
    fill=None, line=None, lw=None, rad=None,
    bold=False, color="#FFFFFF", font="Arial",
    align="center", anchor="middle", margin_pt=3, autofit=False,
    fit_to_shape=True, circle=False, pad_frac=None, wrap=False,
):
    """Create a shape and put `text` in its text frame (not a floating text box)."""
    sh = add_shape(slide, typ, l, t, w, h, fill=fill, line=line, lw=lw, rad=rad)
    set_shape_text(
        sh, text, size_pt, bold=bold, color=color, font=font,
        align=align, anchor=anchor, margin_pt=margin_pt, autofit=autofit,
        fit_to_shape=fit_to_shape, circle=circle, pad_frac=pad_frac, wrap=wrap,
    )
    return sh


_CONNECTOR_KIND = {
    "straight": MSO_CONNECTOR.STRAIGHT,
    "elbow": MSO_CONNECTOR.ELBOW,
    "curve": MSO_CONNECTOR.CURVE,
}


def add_line(slide, x1, y1, x2, y2, color="#000000", width=Pt(1.5), dash=None,
             begin_arrow=None, end_arrow=None, arrow_size="sm", kind="straight"):
    """Real PPT **Line connector** (Format Shape → Line).

    Always a connector — never a thin rectangle or Arrow AutoShape.
    `kind`: straight | elbow | curve  (photo path → property).
    `begin_arrow` / `end_arrow`: triangle | open | stealth | … (photo arrowheads
    → Line Begin/End Arrow property). Both are first-class line properties.
    """
    conn = _CONNECTOR_KIND.get(kind, MSO_CONNECTOR.STRAIGHT)
    sh = slide.shapes.add_connector(conn, x1, y1, x2, y2)
    sh.line.color.rgb = rgb(color) if isinstance(color, str) else color
    sh.line.width = width
    if dash is not None:
        sh.line.dash_style = dash
    set_line_arrows(sh, begin=begin_arrow, end=end_arrow, size=arrow_size)
    disable_shadow(sh)
    return sh


def fan_out_lines(
    slide, origin, targets, *, color="#000000", width=Pt(1.5),
    kind="curve", mid_kind="straight", end_arrow="triangle", arrow_size="sm",
    name_prefix="fan",
):
    """1→N connectors from one origin (x,y) to target points [(x,y), …].

    Photo bracket fans (rounded elbows + arrow tips on each target): use
    `kind=\"curve\"` (or `elbow`) and `end_arrow` on **every** spoke. The
    middle spoke defaults to `mid_kind=\"straight\"` when targets are sorted
    by y; pass `mid_kind=None` to use `kind` for all.
    """
    ox, oy = origin
    ordered = sorted(enumerate(targets), key=lambda it: it[1][1])
    mid_i = ordered[len(ordered) // 2][0] if ordered else -1
    out = []
    for i, (tx, ty) in enumerate(targets):
        use = mid_kind if (mid_kind is not None and i == mid_i) else kind
        sh = add_line(
            slide, ox, oy, tx, ty,
            color=color, width=width, kind=use,
            end_arrow=end_arrow, arrow_size=arrow_size,
        )
        sh.name = f"{name_prefix}_{i}"
        out.append(sh)
    return out


# OOXML arrowhead types shown in Format Shape → Line → Begin/End Arrow
_ARROW_TYPE = {
    None: None,
    "none": None,
    "triangle": "triangle",
    "arrow": "triangle",
    "stealth": "stealth",
    "diamond": "diamond",
    "oval": "oval",
    "open": "arrow",
}
_ARROW_SIZE = {"sm": "sm", "small": "sm", "med": "med", "medium": "med",
               "lg": "lg", "large": "lg"}


def set_line_arrows(shape, begin=None, end=None, size="sm"):
    """Set PowerPoint line arrowheads (Format Shape → Line → Begin/End Arrow).

    Never fake an arrow with MSO_SHAPE.RIGHT_ARROW. `begin` is headEnd
    (start of the connector); `end` is tailEnd.
    """
    ln = shape.line._get_or_add_ln()
    for tag in ("a:headEnd", "a:tailEnd"):
        el = ln.find(qn(tag))
        if el is not None:
            ln.remove(el)
    sz = _ARROW_SIZE.get(size, "sm")
    b = _ARROW_TYPE.get(begin, begin)
    e = _ARROW_TYPE.get(end, end)
    if b:
        etree.SubElement(ln, qn("a:headEnd"), {"type": str(b), "w": sz, "len": sz})
    if e:
        etree.SubElement(ln, qn("a:tailEnd"), {"type": str(e), "w": sz, "len": sz})
    return shape


def stroke_px_to_pt(stroke_px, img_h, slide_h_in=7.5):
    """Screenshot stroke thickness → line width in points."""
    if not stroke_px or img_h <= 0:
        return 1.0
    return max(0.5, round(float(stroke_px) / float(img_h) * float(slide_h_in) * 72.0, 2))


def classify_rect_corner(im, box, stroke_fn=None, max_r=24):
    """Ask every rectangle: sharp corner or round?

    Inspect the top-left corner of `box`=(x,y,w,h) on the screenshot.

    Returns dict:
      class: "sharp" | "slight" | "round"
      radius_px: estimated corner cut in pixels
      rad: python-pptx ROUNDED_RECTANGLE adjustments[0] (0 for sharp → use RECTANGLE)
      shape: MSO_SHAPE.RECTANGLE or MSO_SHAPE.ROUNDED_RECTANGLE

    Rule: never default to rounded. Classify from the photo.
    """
    if Image is None:
        raise RuntimeError("Pillow is required")
    rgb = im.convert("RGB") if getattr(im, "mode", None) != "RGB" else im
    px = rgb.load()
    x, y, w, h = [int(v) for v in box]
    W, H = rgb.size

    def default_stroke(r, g, b):
        # Generic non-white, non-near-white edge (works for gold/gray/black strokes)
        L = (r + g + b) / 3.0
        if L > 245:
            return False
        if abs(r - g) < 12 and abs(g - b) < 12 and L > 200:
            return False  # soft fill
        return L < 230

    is_stroke = stroke_fn or default_stroke

    def hit(xx, yy):
        if not (0 <= xx < W and 0 <= yy < H):
            return False
        return bool(is_stroke(*px[xx, yy]))

    corner_stroke = hit(x, y)
    top_start = None
    for dx in range(0, min(max_r + 5, w)):
        if hit(x + dx, y):
            top_start = dx
            break
    left_start = None
    for dy in range(0, min(max_r + 5, h)):
        if hit(x, y + dy):
            left_start = dy
            break
    bg_cut = 0
    for r in range(0, max_r):
        if (not hit(x + r, y)) and (not hit(x, y + r)):
            bg_cut = r + 1
        else:
            break

    if corner_stroke and (top_start or 0) <= 1 and (left_start or 0) <= 1:
        cls, radius_px = "sharp", 0
    else:
        radius_px = max(top_start or 0, left_start or 0, bg_cut)
        if radius_px >= 8:
            cls = "round"
        elif radius_px >= 3:
            cls = "slight"
        else:
            cls = "sharp"
            radius_px = 0

    if cls == "sharp":
        return {
            "class": "sharp",
            "radius_px": 0,
            "rad": 0.0,
            "shape": MSO_SHAPE.RECTANGLE,
        }
    # Map px radius → adjustments[0] ≈ r / (min_side/2) style; clamp to useful range
    adj = radius_px / max(1.0, min(w, h) / 2.0)
    adj = max(0.02, min(0.5, round(adj, 3)))
    return {
        "class": cls,
        "radius_px": radius_px,
        "rad": adj,
        "shape": MSO_SHAPE.ROUNDED_RECTANGLE,
    }


def measure_stroke_px(im, x, y, axis="v", dark=200, span=18):
    """Perpendicular run-length of dark ink at (x,y). axis='v' for a horizontal line."""
    if Image is None:
        raise RuntimeError("Pillow is required")
    rgb = im.convert("RGB") if im.mode != "RGB" else im
    px = rgb.load()
    w, h = rgb.size

    def darkish(xx, yy):
        if not (0 <= xx < w and 0 <= yy < h):
            return False
        r, g, b = px[xx, yy]
        return (r + g + b) / 3 < dark

    best = 0
    if axis == "v":
        for x0 in range(max(0, x - 6), min(w, x + 7)):
            run = 0
            for yy in range(max(0, y - span), min(h, y + span + 1)):
                if darkish(x0, yy):
                    run += 1
                    best = max(best, run)
                else:
                    run = 0
    else:
        for y0 in range(max(0, y - 6), min(h, y + 7)):
            run = 0
            for xx in range(max(0, x - span), min(w, x + span + 1)):
                if darkish(xx, y0):
                    run += 1
                    best = max(best, run)
                else:
                    run = 0
    return best


def add_crosshair_marker(
    slide,
    *,
    cx_in,
    track_y_in,
    stem_top_in,
    thumb_d_in,
    track_color,
    stem_color,
    circle_color,
    track_pt,
    stem_pt,
    add_track=False,
    track_x0_in=None,
    track_x1_in=None,
    group_name="selected_marker",
):
    """Build a stacked slider/crosshair marker (universal composite).

    Roles (z bottom→top):
      1. grey horizontal track (optional here — often drawn once for the whole slider)
      2. grey vertical stem
      3. accent circle centered on the track

    Stem color MUST match track grey family — never the circle accent.
    Returns (group_or_shapes, thumb_shape).
    """
    shapes = []
    if add_track:
        if track_x0_in is None or track_x1_in is None:
            raise ValueError("add_track requires track_x0_in / track_x1_in")
        shapes.append(
            add_line(
                slide, track_x0_in, track_y_in, track_x1_in, track_y_in,
                color=track_color, width=Pt(track_pt),
            )
        )
    stem = add_line(
        slide, cx_in, stem_top_in, cx_in, track_y_in,
        color=stem_color, width=Pt(stem_pt),
    )
    r = float(thumb_d_in) / 2.0
    thumb = add_shape(
        slide, MSO_SHAPE.OVAL,
        cx_in - r, track_y_in - r, thumb_d_in, thumb_d_in,
        fill=circle_color, line=None,
    )
    thumb.name = "blue_thumb"
    grp = group_shapes(slide, [stem, thumb], name=group_name)
    return grp, thumb


# Connection sites on a shape bounding box (python-pptx convention):
# 0 = top, 1 = left, 2 = bottom, 3 = right
CXN_TOP, CXN_LEFT, CXN_BOTTOM, CXN_RIGHT = 0, 1, 2, 3


def connect_shapes(
    slide, start_shape, start_idx, end_shape, end_idx,
    color="#000000", width=Pt(1.5), kind="straight", dash=None,
    begin_arrow=None, end_arrow=None, arrow_size="sm",
):
    """Attach a connector to two shapes so it stays connected in PowerPoint.

    Circles use the same 4 bbox sites; those land on N/E/S/W of the oval.
    Create the two shapes first, then this connector. Arrowheads are line
    properties (Format Shape → Line), not arrow AutoShapes.

    `kind`: detect from the screenshot — "straight", "elbow" (right angles),
    or "curve" (smooth arcs; PowerPoint Curved Connector / Curve look).
    Do not default to elbow when the photo shows smooth bends.
    """
    def _pt(shape, idx):
        x, y, w, h = int(shape.left), int(shape.top), int(shape.width), int(shape.height)
        return {
            0: (x + w // 2, y),
            1: (x, y + h // 2),
            2: (x + w // 2, y + h),
            3: (x + w, y + h // 2),
        }[idx]

    x1, y1 = _pt(start_shape, start_idx)
    x2, y2 = _pt(end_shape, end_idx)
    sh = slide.shapes.add_connector(_CONNECTOR_KIND.get(kind, MSO_CONNECTOR.STRAIGHT), x1, y1, x2, y2)
    sh.begin_connect(start_shape, start_idx)
    sh.end_connect(end_shape, end_idx)
    sh.line.color.rgb = rgb(color) if isinstance(color, str) else color
    sh.line.width = width
    if dash is not None:
        sh.line.dash_style = dash
    set_line_arrows(sh, begin=begin_arrow, end=end_arrow, size=arrow_size)
    disable_shadow(sh)
    return sh


def connect_lr(slide, a, b, color="#000000", width=Pt(1.5), kind="straight", dash=None,
               begin_arrow=None, end_arrow=None, arrow_size="sm"):
    """Connect a's right site to b's left site."""
    return connect_shapes(
        slide, a, CXN_RIGHT, b, CXN_LEFT, color, width, kind, dash,
        begin_arrow=begin_arrow, end_arrow=end_arrow, arrow_size=arrow_size,
    )


def inset_box(box, pad=0, pad_l=None, pad_t=None, pad_r=None, pad_b=None):
    """Shrink a pixel box by padding. Uniform `pad` or per-side overrides."""
    x, y, w, h = [float(v) for v in box]
    l = pad if pad_l is None else pad_l
    t = pad if pad_t is None else pad_t
    r = pad if pad_r is None else pad_r
    b = pad if pad_b is None else pad_b
    return (x + l, y + t, max(1.0, w - l - r), max(1.0, h - t - b))


def center_in(parent, child_w, child_h):
    """Pixel box for a child of size (child_w, child_h) centered in parent."""
    px, py, pw, ph = [float(v) for v in parent]
    return (px + (pw - child_w) / 2.0, py + (ph - child_h) / 2.0, child_w, child_h)


def band(parent, y0_frac, y1_frac):
    """Horizontal band inside parent from y0_frac→y1_frac of parent height."""
    x, y, w, h = [float(v) for v in parent]
    t = y + h * y0_frac
    b = y + h * y1_frac
    return (x, t, w, max(1.0, b - t))


def label_above(cx, cy, node_r, text_w, text_h, gap=6):
    """Label box centered above a circular node."""
    return (cx - text_w / 2.0, cy - node_r - gap - text_h, text_w, text_h)


def label_below(cx, cy, node_r, text_w, text_h, gap=6):
    """Label box centered below a circular node."""
    return (cx - text_w / 2.0, cy + node_r + gap, text_w, text_h)


def label_centered_on_box(parent_box, ink_w, ink_h, *, side="above", gap_px=8):
    """Place a label centered on a parent box edge (title above a card, etc.).

    Horizontal: parent_cx − ink_w/2 (always optically centered on the box).
    Vertical: measured gap from the facing edge — never a guessed wider host box.
    """
    px, py, pw, ph = [float(v) for v in parent_box]
    cx = px + pw / 2.0
    x = cx - float(ink_w) / 2.0
    if side in ("above", "top"):
        y = py - float(gap_px) - float(ink_h)
    elif side in ("below", "bottom"):
        y = py + ph + float(gap_px)
    else:
        raise ValueError("side must be above/below")
    return (round(x), round(y), round(float(ink_w)), round(float(ink_h)))


def text_in_corridor(
    bound_top=None,
    bound_bottom=None,
    bound_left=None,
    bound_right=None,
    *,
    gap_above=None,
    gap_below=None,
    gap_left=None,
    gap_right=None,
    ink_w=None,
    ink_h=None,
    equal_gaps=False,
):
    """Place a text box from measured gaps to neighboring shapes/lines.

    Use when text sits *between* connectors, rules, or container edges
    (e.g. "Tool usage" between dual arrows, "Cost" between vertical arrows).

    Pass the bounding edge coordinates (line y / x, or shape edge) and the
    measured px gaps from the photo. Do **not** center in leftover space and
    do **not** let the placeholder overlap a neighbor.

    `equal_gaps=True`: ignore asymmetric measured side gaps and split the
    free space evenly (user/photo intent = optically centered between lines).

    Returns (x, y, w, h) in screenshot px.
    """
    if ink_w is None or ink_h is None:
        raise ValueError("ink_w and ink_h required")
    w, h = float(ink_w), float(ink_h)

    if equal_gaps:
        if None in (bound_left, bound_right, bound_top, bound_bottom):
            raise ValueError("equal_gaps needs all four bounds")
        span_x = float(bound_right) - float(bound_left)
        span_y = float(bound_bottom) - float(bound_top)
        if w > span_x - 2 or h > span_y - 2:
            raise ValueError(
                f"ink {w}x{h} does not fit corridor "
                f"{span_x:.0f}x{span_y:.0f}"
            )
        x = float(bound_left) + (span_x - w) / 2.0
        y = float(bound_top) + (span_y - h) / 2.0
        return (round(x), round(y), round(w), round(h))

    if bound_top is not None and gap_above is not None:
        y = float(bound_top) + float(gap_above)
    elif bound_bottom is not None and gap_below is not None:
        y = float(bound_bottom) - float(gap_below) - h
    else:
        raise ValueError("need (bound_top,gap_above) or (bound_bottom,gap_below)")

    if bound_left is not None and gap_left is not None:
        x = float(bound_left) + float(gap_left)
    elif bound_right is not None and gap_right is not None:
        x = float(bound_right) - float(gap_right) - w
    else:
        raise ValueError("need (bound_left,gap_left) or (bound_right,gap_right)")

    # Hard no-overlap: box must stay inside corridor
    if bound_top is not None and y < float(bound_top) + 1:
        raise ValueError(f"text overlaps top bound: y={y} top={bound_top}")
    if bound_bottom is not None and y + h > float(bound_bottom) - 1:
        raise ValueError(
            f"text overlaps bottom bound: y+h={y+h} bottom={bound_bottom}"
        )
    if bound_left is not None and x < float(bound_left) + 1:
        raise ValueError(f"text overlaps left bound: x={x} left={bound_left}")
    if bound_right is not None and x + w > float(bound_right) - 1:
        raise ValueError(
            f"text overlaps right bound: x+w={x+w} right={bound_right}"
        )
    return (round(x), round(y), round(w), round(h))


def add_line_text(slide, l, t, w, h, text, size_pt, bold=False, color="#1A1A1A",
                  align="left", font="Arial", anchor="middle"):
    """One visual line. wrap=False so PPT never wraps a measured glyph box."""
    return add_text(
        slide, l, t, w, h, text, size_pt, bold=bold, color=color,
        align=align, font=font, auto_fit=False, anchor=anchor, wrap=False,
    )


def text_in_box(slide, box_px, text, size_pt, img_w, img_h, slide_w=13.33, slide_h=7.5,
                fit="height", bold=False, color="#1A1A1A", align="center", font="Arial",
                pad=2, wrap=False, anchor="middle"):
    """Place text in a container box (parent inset).

    `wrap=False` (default): one visual line — measured labels, titles.
    `wrap=True`: PowerPoint placeholder flow — paragraph wraps inside the box
    width (captions that break to the next line in the screenshot).
    """
    x, y, w, h = inset_box(box_px, pad=pad)
    l, t, ww, hh = px_box_to_inches(x, y, w, h, img_w, img_h, slide_w, slide_h, fit)
    if wrap:
        return add_text(
            slide, l, t, ww, hh, text, size_pt,
            bold=bold, color=color, align=align, font=font,
            auto_fit=False, anchor=anchor, wrap=True,
        )
    return add_line_text(
        slide, l, t, ww, hh, text, size_pt,
        bold=bold, color=color, align=align, font=font, anchor=anchor,
    )


def caption_band_box(card_box, diagram_box, pad_top_px, pad_bot_px, side_pad_px=10):
    """Placeholder box for a caption under a diagram, from measured gaps.

    Measure on the screenshot:
      pad_top = distance from diagram bottom edge → caption ink top
      pad_bot = distance from caption ink bottom → next element / card bottom
    Width ≈ card width − 2×side_pad (or measured ink width + side pad).
    Alignment is usually center for card footers; left for callouts beside nodes.
    """
    cx, cy, cw, ch = [float(v) for v in card_box]
    _dx, _dy, _dw, dh = [float(v) for v in diagram_box]
    diag_bottom = _dy + dh
    y = diag_bottom + float(pad_top_px)
    # Prefer explicit bottom pad from card bottom when provided
    h = (cy + ch - float(pad_bot_px)) - y
    if h < 12:
        h = 12.0
    x = cx + float(side_pad_px)
    w = max(20.0, cw - 2 * float(side_pad_px))
    return (x, y, w, h)


def abs_in_parent(parent_box, local_xywh):
    """Convert parent-local (x,y,w,h) → absolute screenshot/slide px box."""
    px, py, pw, ph = [float(v) for v in parent_box]
    lx, ly, lw, lh = [float(v) for v in local_xywh]
    return (px + lx, py + ly, lw, lh)


def pads_in_parent(parent_box, child_box):
    """Measured insets of child inside parent: pad_L/T/R/B in px.

    Position children from these — never invent equal padding or center leftover space.
    """
    px, py, pw, ph = [float(v) for v in parent_box]
    cx, cy, cw, ch = [float(v) for v in child_box]
    return {
        "pad_L": round(cx - px, 1),
        "pad_T": round(cy - py, 1),
        "pad_R": round((px + pw) - (cx + cw), 1),
        "pad_B": round((py + ph) - (cy + ch), 1),
    }


def nested_row_from_pads(host_box, *, pad_L, pad_T, body_w, body_h, hgap, n):
    """Rebuild n equal sibling boxes inside a host from measured pads + gap.

    Formula (screenshot px):
      body[i] = (host.x + pad_L + i*(body_w + hgap),
                 host.y + pad_T,
                 body_w, body_h)

    Use after measuring host, first/last child pads, uniform body size, and
    sibling hgap on the photo. Do not guess padding inside the dashed/stroked host.
    """
    hx, hy = float(host_box[0]), float(host_box[1])
    bw, bh = float(body_w), float(body_h)
    gap = float(hgap)
    pl, pt = float(pad_L), float(pad_T)
    return [
        (round(hx + pl + i * (bw + gap)), round(hy + pt), round(bw), round(bh))
        for i in range(int(n))
    ]


def badge_on_body_top(body_box, diameter, cx_frac=0.5):
    """Overlay badge docked to body top edge (cy = body.top). Half outside.

    Prefer badge_inside_body_top when the photo shows the circle fully inside.
    """
    bx, by, bw, _bh = [float(v) for v in body_box]
    d = float(diameter)
    cx = bx + bw * float(cx_frac)
    return (cx - d / 2.0, by - d / 2.0, d, d)


def badge_inside_body_top(body_box, diameter, pad_T=2.0, cx_frac=0.5):
    """Badge fully inside body near top. pad_T = body.top → badge.top (px)."""
    bx, by, bw, bh = [float(v) for v in body_box]
    d = float(diameter)
    pt = float(pad_T)
    if pt + d > bh:
        pt = max(0.0, bh - d)
    cx = bx + bw * float(cx_frac)
    return (cx - d / 2.0, by + pt, d, d)


def measure_dashed_lines_under(px, body_box, below_y, *, expect_n=None, thr=140, min_runs=3, min_n=6):
    """Find horizontal dashed content lines inside body_box below below_y.

    Universal (any screenshot): count and y from the photo — never invent
    fractions of parent height. Returns dict with line_ys, gaps, x fracs, or None.
    """
    bx, by, bw, bh = [int(v) for v in body_box]
    y_lo = int(below_y) + 1
    y_hi = by + bh - 2
    hits = []
    for y in range(y_lo, y_hi):
        runs = n = 0
        inrun = False
        xs = []
        for x in range(bx + 4, bx + bw - 4):
            c = px[x, y]
            v = c[0] >= thr and c[1] >= thr and c[2] >= thr
            if v:
                n += 1
                xs.append(x)
            if v and not inrun:
                runs += 1
                inrun = True
            elif not v:
                inrun = False
        if runs >= min_runs and n >= min_n:
            hits.append((y, n, runs, min(xs), max(xs)))
    if not hits:
        return None
    clusters = [[hits[0]]]
    for h in hits[1:]:
        if h[0] - clusters[-1][-1][0] <= 2:
            clusters[-1].append(h)
        else:
            clusters.append([h])
    centers, x_spans = [], []
    for c in clusters:
        best = max(c, key=lambda t: t[1])
        centers.append(best[0])
        x_spans.append((best[3], best[4]))
    if expect_n is not None:
        centers = centers[: int(expect_n)]
        x_spans = x_spans[: int(expect_n)]
        if len(centers) < int(expect_n):
            return None
    gaps = [centers[i + 1] - centers[i] for i in range(len(centers) - 1)]
    x0 = min(s[0] for s in x_spans)
    x1 = max(s[1] for s in x_spans)
    return {
        "line_ys": centers,
        "line_y_fracs": [round((y - by) / bh, 3) for y in centers],
        "anchor_to_line0": round(centers[0] - float(below_y), 1),
        "inter_line_gap": round(sum(gaps) / len(gaps), 1) if gaps else None,
        "line_x0_frac": round((x0 - bx) / bw, 3),
        "line_x1_frac": round((x1 - bx) / bw, 3),
        "n_lines": len(centers),
    }


def lines_under_anchor(body_box, anchor_box, *, gap0, n, inter_gap, x0_frac=0.2, x1_frac=0.8):
    """Place n horizontal line segments under an anchor from measured gaps.

    y[0] = anchor.bottom + gap0; y[i] = y[0] + i * inter_gap.
    Returns list of (x0, y, x1, y) in screenshot px.
    """
    bx, _by, bw, _bh = [float(v) for v in body_box]
    anchor_bot = float(anchor_box[1]) + float(anchor_box[3])
    x0 = bx + bw * float(x0_frac)
    x1 = bx + bw * float(x1_frac)
    y0 = anchor_bot + float(gap0)
    step = float(inter_gap)
    return [(x0, y0 + i * step, x1, y0 + i * step) for i in range(int(n))]


def child_fits(parent_box, child_box, slack_px=2):
    """True if child is inside parent (optional slack for AA / intentional overlap)."""
    px, py, pw, ph = [float(v) for v in parent_box]
    cx, cy, cw, ch = [float(v) for v in child_box]
    return (
        cx >= px - slack_px
        and cy >= py - slack_px
        and cx + cw <= px + pw + slack_px
        and cy + ch <= py + ph + slack_px
    )


def assert_children_inside(parent_box, children, slack_px=2):
    """Raise if any named child overflows the nested parent.

    `children` is [{name, box_px}, ...]. Use after measuring layout and
    BEFORE grouping — overflow inside a group is what PowerPoint shows as
    piled / overlapping members when the group is selected.
    """
    bad = []
    for ch in children:
        box = ch.get("box_px") or ch.get("box")
        name = ch.get("name") or ch.get("id") or "?"
        if box is None:
            continue
        if not child_fits(parent_box, box, slack_px=slack_px):
            bad.append(f"{name} box={list(map(int, box))} ⊄ parent={list(map(int, parent_box))}")
    if bad:
        raise ValueError(
            "nested children overflow parent (fix layout / nest pads):\n  - "
            + "\n  - ".join(bad)
        )


def point_on_edge(box, side, t=0.5):
    """Pixel point on a box edge. `t` in [0,1] along the edge (0=start).

    sides: left / right / top / bottom. Used so connectors terminate ON the
    stroke, not at a shared center that piles every spoke on one pixel.
    """
    x, y, w, h = [float(v) for v in box]
    t = max(0.0, min(1.0, float(t)))
    if side in ("left", "l"):
        return (x, y + h * t)
    if side in ("right", "r"):
        return (x + w, y + h * t)
    if side in ("top", "t"):
        return (x + w * t, y)
    if side in ("bottom", "b"):
        return (x + w * t, y + h)
    raise ValueError(f"unknown side {side!r}")


def edge_attach_ts(n, margin=0.12):
    """Evenly spaced `t` values along an edge for n fan-in/out spokes.

    Avoids the classic defect where every connector ends at the mid-point
    and the strokes look like one thick overlapping bundle.
    """
    n = int(n)
    if n <= 0:
        return []
    if n == 1:
        return [0.5]
    lo, hi = float(margin), 1.0 - float(margin)
    if n == 2:
        return [lo, hi]
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def uniform_stack(y0, h, gap, n):
    """n boxes of height h with constant gap — sibling rows from photo measure."""
    return [float(y0) + i * (float(h) + float(gap)) for i in range(int(n))]


def assert_min_gap(a_box, b_box, axis, min_px, name=""):
    """Raise if two axis-aligned boxes are closer than min_px (or overlap)."""
    ax, ay, aw, ah = [float(v) for v in a_box]
    bx, by, bw, bh = [float(v) for v in b_box]
    if axis == "x":
        if ax + aw <= bx:
            gap = bx - (ax + aw)
        elif bx + bw <= ax:
            gap = ax - (bx + bw)
        else:
            gap = -1.0
    elif axis == "y":
        if ay + ah <= by:
            gap = by - (ay + ah)
        elif by + bh <= ay:
            gap = ay - (by + bh)
        else:
            gap = -1.0
    else:
        raise ValueError("axis must be 'x' or 'y'")
    if gap < float(min_px):
        tag = f" ({name})" if name else ""
        raise ValueError(
            f"gap too small{tag}: {gap:.1f}px < {min_px}px "
            f"a={list(map(int, a_box))} b={list(map(int, b_box))}"
        )


def add_flow_text(slide, l, t, w, h, text, size_pt, bold=False, color="#1A1A1A",
                  align="center", font="Arial", anchor="middle"):
    """One text-box placeholder: word wrap on, text flows to the next line.

    Use when the screenshot shows a wrapped paragraph (caption under a card),
    not when each line is a separately measured label.
    """
    return add_text(
        slide, l, t, w, h, text, size_pt,
        bold=bold, color=color, align=align, font=font,
        auto_fit=False, anchor=anchor, wrap=True,
    )


def add_text_from_hint(
    slide, hint, text=None, color="#1A1A1A", font="Arial", bold=False,
    script=None, img_w=None, img_h=None, slide_w=13.33, slide_h=7.5,
    fit="height", align="left",
):
    """Place a single-line text box from a text_hints.py record."""
    script = script or hint.get("script") or "latin"
    key = "size_group_font_pt_cjk" if script == "cjk" else "size_group_font_pt_latin"
    size = hint[key]
    x, y, w, h = hint["box_px"]
    x, y, w, h = pad_ink_box_px(x, y, w, h, img_w=img_w, img_h=img_h)
    l, t, ww, hh = px_box_to_inches(x, y, w, h, img_w, img_h, slide_w, slide_h, fit)
    return add_line_text(
        slide, l, t, ww, hh, text if text is not None else hint.get("text", ""),
        size, bold=bold, color=color, align=align, font=font,
    )


def add_text(slide, l, t, w, h, text, size_pt, bold=False, color="#1A1A1A",
             align="center", font="Arial", auto_fit=False, anchor="middle",
             wrap=True, margin_pt=0):
    """Text box. Photo soft-wraps become separate paragraphs when `text` contains \\n."""
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    if auto_fit:
        tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
    if anchor == "middle":
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    elif anchor == "bottom":
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
    else:
        tf.vertical_anchor = MSO_ANCHOR.TOP
    m = Pt(margin_pt)
    tf.margin_left = m
    tf.margin_right = m
    tf.margin_top = m
    tf.margin_bottom = m

    lines = str(text).split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if i == 0:
            p.clear()
        p.alignment = ALIGN.get(align, PP_ALIGN.CENTER)
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size_pt)
        run.font.bold = bold
        run.font.color.rgb = rgb(color)
        run.font.name = font
    disable_shadow(tb)
    return tb


def add_shadow(shape, blur=25000, dist=8000, alpha=8000, base="999999",
               dir_angle=90, blur_pt=None, dist_pt=None, transparency_pct=None,
               size_pct=None):
    """Apply outer shadow. Only when Vision / panel marked the element as having one.

    OOXML uses EMUs (12700 = 1 pt) and alpha in thousandths of a percent
    (100000 = fully opaque). Size uses sx/sy in 1000ths of a percent
    (100000 = 100%).

    Prefer the Google-Slides / PPT panel fields when known:
      blur_pt, dist_pt, transparency_pct, size_pct, dir_angle
      (e.g. blur 11, dist 4, transparency 18, size 101, angle 90 = down).
    """
    if blur_pt is not None:
        blur = int(round(float(blur_pt) * 12700))
    if dist_pt is not None:
        dist = int(round(float(dist_pt) * 12700))
    if transparency_pct is not None:
        # transparency 18% → opacity 82% → alpha val 82000
        opacity = max(0.0, min(100.0, 100.0 - float(transparency_pct)))
        alpha = int(round(opacity * 1000))
    # dir: 60000ths of a degree; 90° = straight down
    dir_val = str(int(round(float(dir_angle) * 60000)) % 21600000)

    spPr = shape._element.find(qn("a:spPr"))
    if spPr is None:
        spPr = shape._element
    el = spPr.find(qn("a:effectLst"))
    if el is None:
        el = etree.SubElement(spPr, qn("a:effectLst"))
    existing = el.find(qn("a:outerShdw"))
    if existing is not None:
        el.remove(existing)
    attrs = {
        "blurRad": str(int(blur)),
        "dist": str(int(dist)),
        "dir": dir_val,
        "rotWithShape": "0",
    }
    if size_pct is not None:
        # Panel Size 101% → sx/sy = 101000
        sx = str(int(round(float(size_pct) * 1000)))
        attrs["sx"] = sx
        attrs["sy"] = sx
    os = etree.SubElement(el, qn("a:outerShdw"), attrs)
    sc = etree.SubElement(os, qn("a:srgbClr"), {"val": base.replace("#", "").upper()})
    etree.SubElement(sc, qn("a:alpha"), {"val": str(int(alpha))})
    return shape


def inch_pct(container_origin, container_size, pct):
    """container origin/size as Inches; pct is 0-100. Returns Inches."""
    return container_origin + container_size * pct / 100.0


def cjk_em_in(size_pt: float) -> float:
    """Full-width CJK advance at this point size, in inches (1em)."""
    return float(size_pt) / 72.0


def cjk_centered_substring_box(
    text: str,
    substring: str,
    size_pt: float,
    slide_w_in: float,
    box_top_in: float,
    box_h_in: float,
    pad_x_in: float = 0.03,
    pad_y_in: float = 0.04,
):
    """Slide-absolute Inches (l, t, w, h) for a marker behind a CJK substring.

    The title is assumed centered on the slide. Never measure the marker as a
    second screenshot blob — proofing squiggles and compression inflate it.
    """
    if substring not in text:
        raise ValueError(f"{substring!r} not in {text!r}")
    em = cjk_em_in(size_pt)
    total = len(text) * em
    left = (slide_w_in - total) / 2.0
    i = text.index(substring)
    l = left + i * em - pad_x_in
    w = len(substring) * em + 2 * pad_x_in
    h = min(max(box_h_in - 0.08, em * 0.7), em * 0.92)
    t = box_top_in + (box_h_in - h) / 2.0
    return Inches(l), Inches(t), Inches(w), Inches(h)


def _xfrm_of(el):
    for child in el:
        if child.tag in (qn("p:spPr"), qn("p:grpSpPr")):
            xf = child.find(qn("a:xfrm"))
            if xf is not None:
                return xf
    return el.find(".//" + qn("a:xfrm"))


def _next_cNvPr_id(spTree) -> int:
    ids = [0]
    for n in spTree.iter(qn("p:cNvPr")):
        try:
            ids.append(int(n.get("id", 0)))
        except (TypeError, ValueError):
            pass
    return max(ids) + 1


def add_pill_icon(
    slide, l, t, w, h, stroke,
    fill="#FFFFFF", lw=None, eye_frac=0.26, eye_x=(0.32, 0.68), name="pill",
):
    """Capsule (rounded rect) + two eye dots → one PowerPoint group.

    Composite icons that read as a single glyph (pill shell + inner dots)
    must be grouped. Select once in PowerPoint = one bounding box.
    Connectors stay *outside* this group and attach to the group shape.

    `lw` is the capsule outline weight — usually heavier than diagram
    connectors (measure both on the screenshot; do not reuse one pt).
    """
    if lw is None:
        lw = Pt(2.5)
    body = add_shape(
        slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h,
        fill=fill, line=stroke, lw=lw, rad=0.5,
    )
    eye = h * eye_frac
    ey = t + (h - eye) / 2
    dots = []
    for fx in eye_x:
        dots.append(add_shape(
            slide, MSO_SHAPE.OVAL,
            l + w * fx - eye / 2, ey, eye, eye,
            fill=stroke, line=None,
        ))
    return group_shapes(slide, [body, *dots], name=name)


def group_shapes(slide, shapes, name="Group", nest_groups=False):
    """Group shapes via OOXML so the result scales in PowerPoint.

    PowerPoint world coords are:
        world = grp.off + (child.off - chOff) * (ext / chExt)

    Children MUST be local (origin 0) and chOff MUST be (0, 0). Setting
    chOff to the group's slide origin AND subtracting that origin from
    children (or assigning shape.left/top after the node is inside grpSp)
    double-offsets the group. PowerPoint then parks it at the slide origin
    even though python-pptx .left still looks correct.

    By default, existing groups (e.g. a pill icon) stay on the slide as
    their own groups. Nesting them inside a card group makes PowerPoint
    click-select the inner rounded rect instead of the icon group.
    Pass nest_groups=True only when you truly need a group-of-groups.
    """
    if not shapes:
        return None
    members = []
    for s in shapes:
        if s is None:
            continue
        try:
            if (not nest_groups) and getattr(s, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
                continue
        except Exception:
            pass
        members.append(s)
    if not members:
        return None
    spTree = slide.shapes._spTree
    records = [(s, int(s.left), int(s.top), int(s.width), int(s.height)) for s in members]
    min_x = min(r[1] for r in records)
    min_y = min(r[2] for r in records)
    max_x = max(r[1] + r[3] for r in records)
    max_y = max(r[2] + r[4] for r in records)
    width = max_x - min_x
    height = max_y - min_y

    grpSp = etree.SubElement(spTree, qn("p:grpSp"))
    nvGrpSpPr = etree.SubElement(grpSp, qn("p:nvGrpSpPr"))
    etree.SubElement(nvGrpSpPr, qn("p:cNvPr"), {
        "id": str(_next_cNvPr_id(spTree)),
        "name": name,
    })
    etree.SubElement(nvGrpSpPr, qn("p:cNvGrpSpPr"))
    etree.SubElement(nvGrpSpPr, qn("p:nvPr"))

    grpSpPr = etree.SubElement(grpSp, qn("p:grpSpPr"))
    xfrm = etree.SubElement(grpSpPr, qn("a:xfrm"))
    etree.SubElement(xfrm, qn("a:off"), {"x": str(min_x), "y": str(min_y)})
    etree.SubElement(xfrm, qn("a:ext"), {"cx": str(width), "cy": str(height)})
    etree.SubElement(xfrm, qn("a:chOff"), {"x": "0", "y": "0"})
    etree.SubElement(xfrm, qn("a:chExt"), {"cx": str(width), "cy": str(height)})

    for s, left, top, _w, _h in records:
        sp = s._element
        if sp is grpSp:
            continue
        spTree.remove(sp)
        grpSp.append(sp)
        # XML only. Never assign s.left / s.top after the node is inside grpSp.
        xf = _xfrm_of(sp)
        if xf is None:
            raise RuntimeError(f"group {name}: {s.name} has no a:xfrm")
        off = xf.find(qn("a:off"))
        if off is None:
            raise RuntimeError(f"group {name}: {s.name} has no a:off")
        off.set("x", str(left - min_x))
        off.set("y", str(top - min_y))
    # Return the python-pptx GroupShape wrapper (has .left/.top for connectors).
    for shape in slide.shapes:
        if shape._element is grpSp:
            return shape
    return grpSp


# Re-export common enums so builders can `from helpers import MSO_SHAPE, Inches, Pt`
__all__ = [
    "MSO_SHAPE", "Inches", "Pt", "Emu", "PP_ALIGN", "MSO_ANCHOR", "MSO_AUTO_SIZE",
    "rgb", "new_presentation", "set_background", "disable_shadow",
    "add_shape", "add_shape_with_text", "set_shape_text", "add_text", "add_flow_text",
    "add_line", "add_line_text", "add_text_from_hint", "fan_out_lines",
    "connect_shapes", "connect_lr", "set_line_arrows", "stroke_px_to_pt", "measure_stroke_px",
    "classify_rect_corner", "add_crosshair_marker",
    "CXN_TOP", "CXN_LEFT", "CXN_BOTTOM", "CXN_RIGHT",
    "add_shadow", "add_pill_icon",
    "inch_pct", "group_shapes", "cjk_em_in", "cjk_centered_substring_box",
    "font_pt_from_glyph", "font_pt_fit_shape", "measure_text_in_shape",
    "ink_inside_shape", "expected_glyph_h_px", "pad_ink_box_px",
    "Image",
    "px_box_to_inches", "pct_to_px", "screenshot_mapping",
    "inset_box", "center_in", "band", "label_above", "label_below", "text_in_box",
    "caption_band_box",
    "abs_in_parent", "child_fits", "assert_children_inside",
    "point_on_edge", "edge_attach_ts", "uniform_stack", "assert_min_gap",
]
