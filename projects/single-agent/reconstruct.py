"""Single Agent diagram — SYSTEM.md method."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

prs = Presentation()
W, H = Inches(13.33), Inches(7.5)
prs.slide_width, prs.slide_height = W, H
blank = prs.slide_layouts[6]

WHITE  = RGBColor(0xFF,0xFF,0xFF)
BLACK  = RGBColor(0x00,0x00,0x00)
GREEN  = RGBColor(0x34,0xA8,0x53)
BLUE   = RGBColor(0x42,0x85,0xF4)
ORANGE = RGBColor(0xF4,0xB4,0x00)
LT_BLUE= RGBColor(0xC6,0xD9,0xF1)
GRAY   = RGBColor(0x66,0x66,0x66)
TEXT   = RGBColor(0x09,0x09,0x09)

slide = prs.slides.add_slide(blank)
bg = slide.background; fill = bg.fill; fill.solid(); fill.fore_color.rgb = WHITE

def S(typ,l,t,w,h,fill=None,line=None,lw=None,rad=None):
    s=slide.shapes.add_shape(typ,l,t,w,h)
    if fill: s.fill.solid(); s.fill.fore_color.rgb=fill
    else: s.fill.background()
    if line: s.line.color.rgb=line; s.line.width=lw or Pt(1)
    else: s.line.fill.background()
    if rad is not None: s.adjustments[0]=rad
    s.shadow.inherit = False
    return s

def T(l,t,w,h,txt,sz,bold=False,c=TEXT,al=PP_ALIGN.CENTER):
    tb=slide.shapes.add_textbox(l,t,w,h)
    tf=tb.text_frame; tf.word_wrap=True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p=tf.paragraphs[0]; p.text=txt
    p.font.size=sz; p.font.bold=bold; p.font.color.rgb=c; p.font.name="Poppins"; p.alignment=al
    return tb

# Frame
FX, FY = Inches(1.2), Inches(0.4)
FW, FH = Inches(10.9), Inches(6.7)
S(MSO_SHAPE.ROUNDED_RECTANGLE, FX, FY, FW, FH, line=BLACK, lw=Pt(2), rad=0.03)

def P(xp,yp,wp,hp):
    """Convert % to Inches relative to frame."""
    return FX+FW*xp/100, FY+FH*yp/100, FW*wp/100, FH*hp/100

print("setup done")
# Title
x,y,w,h = P(4,6,24,6)
T(x,y,w,h,"Single agent", Pt(22), bold=True)

# User icon: person avatar (ring + head + body)
x,y,w,h = P(11,42,8,8); BLUE_C = RGBColor(0x42,0x85,0xF4)
S(MSO_SHAPE.OVAL, x, y, w, w, line=BLUE_C, lw=Pt(2.5), fill=None)
hd = w * 0.29
S(MSO_SHAPE.OVAL, x + w/2 - hd/2, y + w*0.30, hd, hd, fill=BLUE_C)
bw = w * 0.58; bh = w * 0.27
S(MSO_SHAPE.ARC, x + w/2 - bw/2, y + w*0.60, bw, bh, fill=BLUE_C)

# Callout 1: "1. User prompts agent"
x,y,w,h = P(6,34,16,5)
S(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, line=GRAY, lw=Pt(1), rad=0.5)
T(x,y,w,h,"1. User prompts agent", Pt(9), c=TEXT, al=PP_ALIGN.CENTER)

# Agent box
x,y,w,h = P(26,33,14,32)
S(MSO_SHAPE.RECTANGLE, x, y, w, h, line=GREEN, lw=Pt(2))
T(x, y+Inches(0.03), w, Inches(0.35), "Agent", Pt(16), bold=True)

# Model box
x,y,w,h = P(57,18,25,17)
S(MSO_SHAPE.RECTANGLE, x, y, w, h, line=BLUE, lw=Pt(2))
T(x, y, w, h, "Model", Pt(18), bold=True)

# Tools box
x,y,w,h = P(57,57,25,28)
S(MSO_SHAPE.RECTANGLE, x, y, w, h, line=BLUE, lw=Pt(2))
T(x, y, w, h, "Tools", Pt(18), bold=True)

# Tool sub-boxes A,B,C
for i, lbl in enumerate(["A","B","C"]):
    x,y,w,h = P(59+i*8, 72, 6, 9)
    S(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=LT_BLUE, rad=0.15)
    tb=T(x,y,w,h,lbl, Pt(10), bold=True, al=PP_ALIGN.CENTER, c=TEXT); tb.text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT

print("boxes done")
# Orange box
x,y,w,h = P(31,13,19,17)
S(MSO_SHAPE.RECTANGLE, x, y, w, h, fill=ORANGE)
T(x+Inches(0.1), y+Inches(0.15), w-Inches(0.2), h-Inches(0.3),
  "Produce a valid, correctly structured request", Pt(9), c=TEXT, al=PP_ALIGN.CENTER)

# Callout 2
x,y,w,h = P(57,8,25,8)
S(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, line=GRAY, lw=Pt(1), rad=0.4)
T(x,y,w,h,"2. Model selects tool B and formats request body", Pt(8), c=TEXT, al=PP_ALIGN.CENTER)

# Callout 3
x,y,w,h = P(58,50,24,5)
S(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, line=GRAY, lw=Pt(1), rad=0.4)
T(x,y,w,h,"3. Agent framework calls tool B", Pt(8), c=TEXT, al=PP_ALIGN.CENTER)

# Callout 4
x,y,w,h = P(19,67,27,8)
S(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, line=GRAY, lw=Pt(1), rad=0.4)
T(x,y,w,h,"4. Model interprets tool B output, generates response", Pt(8), c=TEXT, al=PP_ALIGN.CENTER)

# Connector lines
x1 = FX+FW*0.17; x2 = FX+FW*0.26
S(MSO_SHAPE.RECTANGLE, x1, FY+FH*0.44, x2-x1, 0, fill=GRAY)
S(MSO_SHAPE.RECTANGLE, x1, FY+FH*0.50, x2-x1, 0, fill=GRAY)
S(MSO_SHAPE.RECTANGLE, FX+FW*0.50, FY+FH*0.21, FW*0.07, 0, fill=GRAY)
S(MSO_SHAPE.RECTANGLE, FX+FW*0.40, FY+FH*0.48, FW*0.15, 0, fill=GRAY)
S(MSO_SHAPE.RECTANGLE, FX+FW*0.55, FY+FH*0.21, 0, FH*0.50, fill=GRAY)
S(MSO_SHAPE.RECTANGLE, FX+FW*0.55, FY+FH*0.27, FW*0.02, 0, fill=GRAY)
S(MSO_SHAPE.RECTANGLE, FX+FW*0.55, FY+FH*0.71, FW*0.02, 0, fill=GRAY)

# Add arrowheads on User-Agent lines (triangle shapes)
# Right arrow (user→agent)
ax, ay = FX+FW*0.24, FY+FH*0.44 - Pt(4)
# Left arrow (agent→user) - flip direction
ax2 = FX+FW*0.17 - Inches(0.15)

# Fix: recalculate Agent box position for icon
ax_box = FX + FW*0.26
ay_box = FY + FH*0.33
aw_box = FW*0.14
ah_box = FH*0.32

# Agent face icon inside Agent box
ix = ax_box + aw_box/2 - Inches(0.15)
iy = ay_box + Inches(0.35)
iw = Inches(0.3); ih = Inches(0.2)
S(MSO_SHAPE.OVAL, ix, iy, iw, ih, line=GREEN, fill=None)
dr = Inches(0.04)
S(MSO_SHAPE.OVAL, ix+iw*0.25-dr/2, iy+ih*0.3-dr/2, dr, dr, fill=GREEN)
S(MSO_SHAPE.OVAL, ix+iw*0.7-dr/2, iy+ih*0.3-dr/2, dr, dr, fill=GREEN)
# Mouth line
S(MSO_SHAPE.RECTANGLE, ix+iw*0.3, iy+ih*0.65, iw*0.4, Pt(1.5), fill=GREEN)

# Arrowheads on User-Agent lines (triangle)
# Right arrow
# Left arrow (flipped)

out = "/Users/admin/Synology_Home/AI Project/Powerpoint Design/Single Agent.pptx"
def add_arrow(line_shape, tail=False, head=False):
    spPr = line_shape._element.find(qn('p:spPr'))
    if spPr is None: spPr = line_shape._element
    ln = spPr.find(qn('a:ln'))
    if ln is None:
        ln = etree.SubElement(spPr, qn('a:ln'))
    if tail:
        etree.SubElement(ln, qn('a:tailEnd'), {'type':'triangle', 'w':'sm', 'len':'sm'})
    if head:
        etree.SubElement(ln, qn('a:headEnd'), {'type':'triangle', 'w':'sm', 'len':'sm'})

# Right arrow: line with arrowhead
ra = S(MSO_SHAPE.RECTANGLE, FX+FW*0.17, FY+FH*0.44, FX+FW*0.24-FX-FW*0.17, 0, fill=GRAY)
add_arrow(ra, head=True)

# Left arrow: line with arrowhead reversed
la = S(MSO_SHAPE.RECTANGLE, FX+FW*0.17, FY+FH*0.50, FX+FW*0.24-FX-FW*0.17, 0, fill=GRAY)
add_arrow(la, tail=True)
prs.save(out)
print(f"Saved: {out}")
