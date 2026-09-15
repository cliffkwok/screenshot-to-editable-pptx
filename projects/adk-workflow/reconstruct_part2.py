"""Part 2 — Top row card: Sequential (blue)"""
from reconstruct_part1 import *

def make_top_card(x,y,w,h,header_text,header_bg,footer_text):
    """Create a top-row card with header bar + content area."""
    # Card background
    S(MSO_SHAPE.RECTANGLE, x, y, w, h, fill=WHITE, line=GRAY, lw=Pt(1))
    # Header bar
    S(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.35), fill=header_bg)
    T(x, y, w, Inches(0.35), header_text, Pt(12), bold=True, c=WHITE)
    # Footer text
    fy = y + h - Inches(0.35)
    T(x+Inches(0.1), fy, w-Inches(0.2), Inches(0.35), footer_text, Pt(8), c=GRAY)
    return y+Inches(0.35), fy  # content area top, bottom


# Sequential card position: x=4-31%, y=20-47%
x,y,w,h = P(4,20,27,27)
ct, cb = make_top_card(x,y,w,h,"Sequential", BLUE_H, "Chains multiple specialized LLMs in a pipeline.")

# Content area
cy_ctr = (ct + cb) / 2
# Circles: Input (blue) → LLM (dark) → LLM (dark) → Output (blue)
cx1 = x + w*0.12; cx2 = x + w*0.38; cx3 = x + w*0.62; cx4 = x + w*0.88
r = Inches(0.28)
card_circle(cx1, cy_ctr, r, BLUE_H, "Input")
card_circle(cx2, cy_ctr, r, BLUE_D, "LLM")
card_circle(cx3, cy_ctr, r, BLUE_D, "LLM")
card_circle(cx4, cy_ctr, r, BLUE_H, "Output")

# Connector lines (thin rectangles)
cx = cx1+r; ex = cx2-r
S(MSO_SHAPE.RECTANGLE, cx, cy_ctr-Pt(0.5), ex-cx, Pt(1), fill=GRAY)
cx = cx2+r; ex = cx3-r
S(MSO_SHAPE.RECTANGLE, cx, cy_ctr-Pt(0.5), ex-cx, Pt(1), fill=GRAY)
cx = cx3+r; ex = cx4-r
S(MSO_SHAPE.RECTANGLE, cx, cy_ctr-Pt(0.5), ex-cx, Pt(1), fill=GRAY)

# Labels above/below
T(cx1+r-Inches(0.5), ct+Inches(0.1), cx3-cx1-Inches(0.1), Inches(0.25), "Intermediate result...", Pt(7), c=GRAY)
T(cx2+r-Inches(0.5), cb-Inches(0.5), cx4-cx2-Inches(0.1), Inches(0.25), "Intermediate Result...", Pt(7), c=GRAY)

print("Part 2 done — Sequential card")