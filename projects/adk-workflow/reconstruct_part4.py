
from reconstruct_part1 import *

# Hierarchical card (red) x=62-99%, y=20-47%
x,y,w,h = P(62,20,37,27)
S(MSO_SHAPE.RECTANGLE, x, y, w, h, fill=WHITE, line=GRAY, lw=Pt(1))
S(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.35), fill=RED)
T(x, y, w, Inches(0.35), "Hierarchical", Pt(12), bold=True, c=WHITE)
fy = y+h-Inches(0.35)
T(x+Inches(0.1), fy, w-Inches(0.2), Inches(0.35), "Router model to direct inputs to specialized LLMs based on content or intent", Pt(8), c=GRAY)
cy = y+Inches(0.35)+(fy-y-Inches(0.35))/2
cx1=x+w*0.07; cx2=x+w*0.40; cx3=x+w*0.88; r=Inches(0.2)
# Input circle
card_circle(cx1, cy, r, RED, "Input")
# Router circle (pink)
card_circle(cx2, y+Inches(0.40)+fy-y-Inches(0.40)*0.12, r*1.2, RED_H, "LLM")
T(cx2-3*r, y+Inches(0.40)+fy-y-Inches(0.40)*0.12-r*2, r*6, r*2, "processing\nRouter", Pt(7), bold=True, c=TEXT)
# Analysis text
T(cx2-3*r, y+Inches(0.40)+fy-y-Inches(0.40)*0.12+r*1.5, r*4, r*1.5, "Analysis and classification", Pt(7), c=GRAY)
# 3 LLM circles (dark red)
offsets = [-Inches(0.6), 0, Inches(0.6)]
for off in offsets:
    S(MSO_SHAPE.OVAL, cx2-off-r, y+Inches(0.40)+fy-y-Inches(0.40)*0.72, r*2, r*2, fill=RED_D)
    T(cx2-off-2*r, y+Inches(0.40)+fy-y-Inches(0.40)*0.72-r*1.5, r*4, r*1.5, "LLM", Pt(7), bold=True, c=WHITE)
# Output circle
card_circle(cx3, cy, r*1.2, RED, "Output")
# Lines from Router to LLMs
for off in offsets:
    S(MSO_SHAPE.RECTANGLE, cx2-off, cy-Pt(0.5), Pt(1), y+Inches(0.40)+fy-y-Inches(0.40)*0.72-cy, fill=GRAY)
# Lines from LLMs to Output
for off in offsets:
    lx = cx2-off+r; ex = cx3-r
    S(MSO_SHAPE.RECTANGLE, lx, y+Inches(0.40)+fy-y-Inches(0.40)*0.72+r*2+Pt(1), ex-lx, Pt(1), fill=GRAY)
# Input→Router line
S(MSO_SHAPE.RECTANGLE, cx1+r, cy-Pt(0.5), cx2-r-cx1-r, Pt(1), fill=GRAY)
S(MSO_SHAPE.RECTANGLE, cx2+r, y+h*0.55, cx3-r-cx2-r, Pt(1), fill=GRAY)
print("Hierarchical card done")
