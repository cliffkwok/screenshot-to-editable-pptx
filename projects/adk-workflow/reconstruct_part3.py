"""ADK agent workflow — remaining cards"""
from reconstruct_part1 import *

# Parallel card (yellow) x=33-60%, y=20-47%
x,y,w,h = P(33,20,27,27)
S(MSO_SHAPE.RECTANGLE, x, y, w, h, fill=WHITE, line=GRAY, lw=Pt(1))
S(MSO_SHAPE.RECTANGLE, x, y, w, Inches(0.35), fill=YELLOW)
T(x, y, w, Inches(0.35), "Parallel", Pt(12), bold=True, c=WHITE)
fy = y+h-Inches(0.35)
T(x+Inches(0.1), fy, w-Inches(0.2), Inches(0.35), "Multiple LLMs concurrently and aggregate outputs", Pt(8), c=GRAY)
cy = y+Inches(0.35)+(fy-y-Inches(0.35))/2
# Input → 3 LLM → Aggregator → Output
cx1=x+w*0.08; cx2=x+w*0.42; cx3=x+w*0.72; cx4=x+w*0.92; r=Inches(0.28)
card_circle(cx1, cy, r, YELLOW_H, "Input")
S(MSO_SHAPE.OVAL, cx2-r, y+Inches(0.35)+(fy-y-Inches(0.35))*0.15, r*2, r*2, fill=YELLOW_D)
T(cx2-3*r, y+Inches(0.35)+(fy-y-Inches(0.35))*0.15-r, r*6, r*1.5, "LLM", Pt(7), bold=True, c=WHITE)
S(MSO_SHAPE.OVAL, cx2-r, cy-r, r*2, r*2, fill=YELLOW_D)
T(cx2-3*r, cy-r*1.5, r*6, r*1.5, "LLM", Pt(7), bold=True, c=WHITE)
S(MSO_SHAPE.OVAL, cx2-r, y+Inches(0.35)+(fy-y-Inches(0.35))*0.85-r, r*2, r*2, fill=YELLOW_D)
T(cx2-3*r, y+Inches(0.35)+(fy-y-Inches(0.35))*0.85-r*2, r*6, r*1.5, "LLM", Pt(7), bold=True, c=WHITE)
card_circle(cx3, cy, r, YELLOW_H, "Aggregator")
card_circle(cx4, cy, r, YELLOW_H, "Output")
# Lines: Input→3 LLM and 3 LLM→Aggregator→Output
for cy_llm in [y+Inches(0.35)+(fy-y-Inches(0.35))*0.15, cy, y+Inches(0.35)+(fy-y-Inches(0.35))*0.85]:
    S(MSO_SHAPE.RECTANGLE, cx1+r, cy_llm-Pt(0.5), cx2-r-cx1-r, Pt(1), fill=GRAY)
    S(MSO_SHAPE.RECTANGLE, cx2+r, cy_llm-Pt(0.5), cx3-r-cx2-r, Pt(1), fill=GRAY)
S(MSO_SHAPE.RECTANGLE, cx3+r, cy-Pt(0.5), cx4-r-cx3-r, Pt(1), fill=GRAY)
print("Parallel card done")
