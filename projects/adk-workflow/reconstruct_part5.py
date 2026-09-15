from reconstruct_part1 import *
def bottom_card(x,y,w,h,title,accent):
    S(MSO_SHAPE.RECTANGLE,x,y,w,h,fill=WHITE,line=CARD_BR,lw=Pt(1))
    T(x,y,w,Inches(0.3),title,Pt(11),bold=True,c=BLACK)
    S(MSO_SHAPE.RECTANGLE,x,y+Inches(0.3),w,Pt(1.5),fill=accent)
    return y+Inches(0.35),y+h
def pill(x,y,accent):
    pw,ph=Inches(0.5),Inches(0.32)
    S(MSO_SHAPE.ROUNDED_RECTANGLE,x,y,pw,ph,fill=accent,rad=0.5)
    S(MSO_SHAPE.OVAL,x+Inches(.13),y+Inches(.08),Inches(.07),Inches(.07),fill=WHITE)
    S(MSO_SHAPE.OVAL,x+Inches(.30),y+Inches(.08),Inches(.07),Inches(.07),fill=WHITE)
    return pw,ph
# 1. Sequential agent (blue)
x,y,w,h = P(4,50,26,47)
ct,cb = bottom_card(x,y,w,h,"Sequential agent",BLUE_H)
cy=(ct+cb)/2; ph_val=Inches(0.32)
for i in range(3):
    px=x+w*0.10+i*w*0.30; py=cy-ph_val/2
    pw,_=pill(px,py,BLUE_H)
    if i<2: S(MSO_SHAPE.RECTANGLE,px+pw,cy-Pt(0.5),x+w*0.10+(i+1)*w*0.30-px-pw,Pt(1.5),fill=GRAY)

# === Collect shapes for grouping ===
def collect_last(n):
    sp = slide.shapes._spTree
    children = list(sp)
    grp_children = [c for c in children if c.tag.endswith('}sp') or c.tag.endswith('}grpSp')]
    return grp_children[-n:] if len(grp_children) >= n else []

print("Seq agent done")

def arrow_h(x1,x2,cy):
    S(MSO_SHAPE.RECTANGLE,x1,cy-Pt(0.5),x2-x1,Pt(1.5),fill=GRAY)

# 2. Parallel agent (yellow)
x,y,w,h = P(32,50,25,47)
ct,cb = bottom_card(x,y,w,h,"Parallel agent",YELLOW)
cy=(ct+cb)/2; ph=Inches(0.32)
for i in range(3):
    py=ct+(cb-ct)*0.15+i*(cb-ct)*0.28
    pill(x+w*0.35,py,YELLOW)
    S(MSO_SHAPE.RECTANGLE,x+w*0.05,py+ph/2-Pt(0.5),x+w*0.35-x-w*0.05,Pt(1.5),fill=GRAY)
print("Parallel agent done")

# 3. Loop agent (red)
x,y,w,h = P(59,50,26,47)
ct,cb = bottom_card(x,y,w,h,"Loop agent",RED)
cy=(ct+cb)/2
pos=[(x+w*0.20,cy-Inches(.3)),(x+w*0.55,cy-Inches(.3)),
     (x+w*0.20,cy+Inches(.3)),(x+w*0.55,cy+Inches(.3))]
for px,py in pos: pill(px,py,RED)
# arrows connecting loop
arrow_h(x+w*0.02,pos[0][0],pos[0][1]+Inches(.16))
arrow_h(pos[0][0]+Inches(.5),pos[1][0],pos[0][1]+Inches(.16))
S(MSO_SHAPE.RECTANGLE,pos[1][0]+Inches(.1),pos[1][1]+Inches(.32),Pt(1.5),pos[3][1]-pos[1][1]-Inches(.16),fill=GRAY)
arrow_h(pos[3][0]+Inches(.5),pos[2][0]+Inches(.5),pos[3][1]+Inches(.16))
S(MSO_SHAPE.RECTANGLE,pos[2][0]+Inches(.1),pos[0][1]+Inches(.32),Pt(1.5),pos[2][1]-pos[0][1]-Inches(.16),fill=GRAY)
print("Loop agent done")

# 4. LLM agent (red)
x,y,w,h = P(87,50,12,47)
ct,cb = bottom_card(x,y,w,h,"LLM agent",RED)
py_bot=cb-Inches(.55)
ps=[(x+w*0.08,py_bot),(x+w*0.35,py_bot),(x+w*0.62,py_bot)]
for px,py in ps: pill(px,py,RED)
apex=x+w*0.42; ay=ct+Inches(.25)
for px,py in ps:
    S(MSO_SHAPE.RECTANGLE,apex,ay,Pt(1),py-ay,fill=GRAY)
print("LLM agent done")
