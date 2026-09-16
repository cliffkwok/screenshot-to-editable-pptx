# python-pptx build notes

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts/

from helpers import (
    new_presentation, set_background, add_shape, add_text,
    add_line_text, add_text_from_hint, add_shadow, disable_shadow,
    group_shapes, inch_pct, MSO_SHAPE, Inches, Pt,
)

prs, slide = new_presentation(13.33, 7.5)
set_background(slide, "#FFFFFF")
```

## Shapes

```python
card = add_shape(
    slide, MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(0.8), Inches(1.2), Inches(5.7), Inches(2.6),
    fill="#FFFFFF", line="#DDDDDD", lw=Pt(1), rad=0.04,
)
# add_shape already calls disable_shadow
add_shadow(card, blur=35000, dist=5000, alpha=7000, base="AAAAAA")  # only if spec says so
```

Pill: `rad=0.5`. Circle: `MSO_SHAPE.OVAL` with equal width and height.

## Text

One visual line = one box. Prefer `add_line_text` (`wrap=False`) or `add_text_from_hint` from `text_hints.py`. Do not guess pt.

```python
add_line_text(
    slide, Inches(2), Inches(0.45), Inches(9.33), Inches(0.55),
    "AI agent design patterns", 38,
    bold=True, color="#202020", align="center", font="Arial",
)
# or
add_text_from_hint(slide, hint, color="#121212", font="Arial", bold=True,
                   img_w=1024, img_h=576, align="center")
```

Prefer Arial unless the screenshot clearly uses another installed face. Missing fonts silently substitute and fail the font gate. CJK: PingFang TC.

## Lines / connectors

For diagram spines, attach connectors to shapes so they stay connected when a node is moved:

```python
from helpers import connect_lr, connect_shapes, CXN_RIGHT, CXN_LEFT
connect_lr(slide, node_a, node_b, "#262626", Pt(1.5))
connect_shapes(slide, src, CXN_RIGHT, dst, CXN_LEFT, "#E66A60", Pt(1.2),
               kind="curve", dash=MSO_LINE.DASH)
```

Sites: 0 top, 1 left, 2 bottom, 3 right. Create both shapes first, then the connector. A free-floating line that only *looks* joined is not attached.

## Text fit

After a first PowerPoint raster, run `scripts/text_fit.py` to measure original vs render ink and nudge `dx/dy` / `font_pt`. Rebuild so spec and PPT stay in sync, then re-audit.

## Colors

Always `RGBColor` via `helpers.rgb("#34A853")`. Theme colors cannot be verified and fail the color gate.

## Grouping

Collect the shapes that belong to one card, then:

```python
group_shapes(slide, card_shapes, name="Single")
```

`group_shapes` writes local child `a:off` and `chOff=(0,0)` via XML. Never assign `.left` / `.top` on those shapes afterwards — PowerPoint will draw the group at the origin.

## Character highlights

```python
from helpers import cjk_centered_substring_box
hl = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE,
               *cjk_centered_substring_box(
                   "常見的初始入侵手段", "入侵", 48, 13.33, title_top, title_h),
               fill="#FFB500", rad=0.12)
```

Do not place the bar from a screenshot rectangle measured separately from the title.

## Save

```python
prs.save("out.pptx")
```

Then inspect and verify — do not skip.
