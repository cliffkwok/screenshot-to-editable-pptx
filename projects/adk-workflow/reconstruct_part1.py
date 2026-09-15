"""ADK agent workflow — Part 1: setup + frame + helpers"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])

WHITE  = RGBColor(0xFF,0xFF,0xFF)
BLACK  = RGBColor(0x00,0x00,0x00)
GRAY   = RGBColor(0x5F,0x63,0x68)
CARD_BR = RGBColor(0xE0,0xE0,0xE0)
TEXT   = RGBColor(0x09,0x09,0x09)

# Color themes (hex from vision analysis)
BLUE_H = RGBColor(0x45,0x83,0xEC)
BLUE_D = RGBColor(0x1A,0x56,0xDB)
YELLOW = RGBColor(0xF5,0xC1,0x44)
YELLOW_H=RGBColor(0xFB,0xBC,0x04)
YELLOW_D=RGBColor(0xE8,0x71,0x0A)
RED    = RGBColor(0xDD,0x3A,0x33)
RED_H  = RGBColor(0xEA,0x99,0x99)
RED_D  = RGBColor(0xC5,0x22,0x1F)

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
    tf=tb.text_frame; tf.word_wrap=True
    p=tf.paragraphs[0]; p.text=txt
    p.font.size=sz; p.font.bold=bold; p.font.color.rgb=c
    p.font.name="Poppins"; p.alignment=al
    return tb

# Main slide frame
FX, FY = Inches(0.3), Inches(0.3)
FW, FH = Inches(12.73), Inches(6.9)
S(MSO_SHAPE.ROUNDED_RECTANGLE, FX, FY, FW, FH, line=BLACK, lw=Pt(2), rad=0.02)

def P(xp,yp,wp,hp):
    """Convert % to Inches relative to frame."""
    return FX+FW*xp/100, FY+FH*yp/100, FW*wp/100, FH*hp/100

# Title
x,y,w,h = P(30,4,40,6)
T(x,y,w,h,"ADK agent - workflow", Pt(24), bold=True)

def card_circle(cx,cy,r,fill_color,label):
    S(MSO_SHAPE.OVAL, cx-r, cy-r, r*2, r*2, fill=fill_color)
    T(cx-r*2, cy-r*0.35, r*4, r*0.7, label, Pt(6), bold=True, c=WHITE)

def group_shapes(name, shapes):
    """Group shapes via XML. Works around python-pptx limitation."""
    if len(shapes) < 2: return
    from lxml import etree
    from pptx.oxml.ns import qn
    parent = shapes[0]._element.getparent()
    grp = etree.SubElement(parent, qn('p:grpSp'))
    nv = etree.SubElement(grp, qn('p:nvGrpSpPr'))
    etree.SubElement(nv, qn('p:cNvPr'), {'id':'0','name':name})
    etree.SubElement(nv, qn('p:cNvGrpSpPr'))
    etree.SubElement(nv, qn('p:nvPr'))
    etree.SubElement(grp, qn('p:grpSpPr'))
    for s in shapes:
        parent.remove(s._element)
        grp.append(s._element)

print("Part 1 done — setup")