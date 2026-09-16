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

Strokes are **connectors** (`add_line` / `connect_shapes`), never thin rectangles and never `RIGHT_ARROW` AutoShapes.

- **Weight:** measure perpendicular ink thickness on the screenshot (`measure_stroke_px`) → `stroke_px_to_pt`. **Do not reuse one weight for every stroke.** A pill/capsule outline is often ~2.5 pt while the gray arrow connector is ~0.75–1 pt on the same slide. Measure outline and connector as separate roles.
- **Arrowheads:** if the photo shows an arrow, set Format Shape → Line → End/Begin Arrow via `end_arrow="triangle"` (OOXML `tailEnd` / `headEnd`). Selecting the line in PowerPoint must show Line properties, not a filled chevron shape.

```python
from helpers import connect_lr, connect_shapes, add_line, CXN_RIGHT, CXN_LEFT, Pt
connect_lr(slide, node_a, node_b, "#8A8A8A", Pt(0.75), end_arrow="triangle")
# Parallel fan: smooth arcs, not elbow corners
connect_shapes(slide, src, CXN_RIGHT, dst, CXN_LEFT, "#E8870A", Pt(1.0), kind="curve")
add_line(slide, x1, y1, x2, y2, color="#8A8A8A", width=Pt(0.75),
         end_arrow="triangle", arrow_size="sm")
```

`kind`: `"straight"` | `"elbow"` | `"curve"`. Detect from the screenshot — sharp 90° bends → elbow; smooth S/C arcs (PowerPoint Curve / Curved Connector) → `curve`.

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

`group_shapes` writes local child `a:off` and `chOff=(0,0)` via XML. Never assign `.left` / `.top` on those shapes afterwards — PowerPoint will draw the group at the origin. It returns the python-pptx `GroupShape` so connectors can attach to the group.

**Composite icons:** capsule + two dots (or any shell + inner marks) must be one group — `add_pill_icon(...)` or `group_shapes([shell, *dots])`. Selecting the icon shows one bbox; leave connectors outside the group.

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
