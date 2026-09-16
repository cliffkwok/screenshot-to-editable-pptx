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
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mapping import (  # noqa: E402
    expected_glyph_h_px,
    font_pt_from_glyph,
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


def add_line(slide, x1, y1, x2, y2, color="#000000", width=Pt(1.5), dash=None):
    """Real PPT connector line (not a thin rectangle). Prefer this for thin strokes."""
    sh = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    sh.line.color.rgb = rgb(color) if isinstance(color, str) else color
    sh.line.width = width
    if dash is not None:
        sh.line.dash_style = dash
    disable_shadow(sh)
    return sh


# Connection sites on a shape bounding box (python-pptx convention):
# 0 = top, 1 = left, 2 = bottom, 3 = right
CXN_TOP, CXN_LEFT, CXN_BOTTOM, CXN_RIGHT = 0, 1, 2, 3
_CONNECTOR_KIND = {
    "straight": MSO_CONNECTOR.STRAIGHT,
    "elbow": MSO_CONNECTOR.ELBOW,
    "curve": MSO_CONNECTOR.CURVE,
}


def connect_shapes(
    slide, start_shape, start_idx, end_shape, end_idx,
    color="#000000", width=Pt(1.5), kind="straight", dash=None,
):
    """Attach a connector to two shapes so it stays connected in PowerPoint.

    Circles use the same 4 bbox sites; those land on N/E/S/W of the oval.
    Create the two shapes first, then this connector.
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
    disable_shadow(sh)
    return sh


def connect_lr(slide, a, b, color="#000000", width=Pt(1.5), kind="straight", dash=None):
    """Connect a's right site to b's left site."""
    return connect_shapes(slide, a, CXN_RIGHT, b, CXN_LEFT, color, width, kind, dash)


def add_line_text(slide, l, t, w, h, text, size_pt, bold=False, color="#1A1A1A",
                  align="left", font="Arial", anchor="middle"):
    """One visual line. wrap=False so PPT never wraps a measured glyph box."""
    return add_text(
        slide, l, t, w, h, text, size_pt, bold=bold, color=color,
        align=align, font=font, auto_fit=False, anchor=anchor, wrap=False,
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
             wrap=True):
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
    p = tf.paragraphs[0]
    p.clear()
    p.alignment = ALIGN.get(align, PP_ALIGN.CENTER)
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = rgb(color)
    run.font.name = font
    disable_shadow(tb)
    return tb


def add_shadow(shape, blur=25000, dist=8000, alpha=8000, base="999999"):
    """Apply outer shadow. Only when Vision marked the element as having one."""
    spPr = shape._element.find(qn("a:spPr"))
    if spPr is None:
        spPr = shape._element
    el = spPr.find(qn("a:effectLst"))
    if el is None:
        el = etree.SubElement(spPr, qn("a:effectLst"))
    existing = el.find(qn("a:outerShdw"))
    if existing is not None:
        el.remove(existing)
    os = etree.SubElement(el, qn("a:outerShdw"), {
        "blurRad": str(blur),
        "dist": str(dist),
        "dir": "5400000",
        "rotWithShape": "0",
    })
    sc = etree.SubElement(os, qn("a:srgbClr"), {"val": base})
    etree.SubElement(sc, qn("a:alpha"), {"val": str(alpha)})
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


def group_shapes(slide, shapes, name="Group"):
    """Group shapes via OOXML so the result scales in PowerPoint.

    PowerPoint world coords are:
        world = grp.off + (child.off - chOff) * (ext / chExt)

    Children MUST be local (origin 0) and chOff MUST be (0, 0). Setting
    chOff to the group's slide origin AND subtracting that origin from
    children (or assigning shape.left/top after the node is inside grpSp)
    double-offsets the group. PowerPoint then parks it at the slide origin
    even though python-pptx .left still looks correct.
    """
    if not shapes:
        return None
    spTree = slide.shapes._spTree
    records = [(s, int(s.left), int(s.top), int(s.width), int(s.height)) for s in shapes]
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
    return grpSp


# Re-export common enums so builders can `from helpers import MSO_SHAPE, Inches, Pt`
__all__ = [
    "MSO_SHAPE", "Inches", "Pt", "Emu", "PP_ALIGN", "MSO_ANCHOR", "MSO_AUTO_SIZE",
    "rgb", "new_presentation", "set_background", "disable_shadow",
    "add_shape", "add_text", "add_line", "add_line_text", "add_text_from_hint",
    "connect_shapes", "connect_lr", "CXN_TOP", "CXN_LEFT", "CXN_BOTTOM", "CXN_RIGHT",
    "add_shadow",
    "inch_pct", "group_shapes", "cjk_em_in", "cjk_centered_substring_box",
    "font_pt_from_glyph", "expected_glyph_h_px", "pad_ink_box_px",
    "px_box_to_inches", "pct_to_px", "screenshot_mapping",
]
