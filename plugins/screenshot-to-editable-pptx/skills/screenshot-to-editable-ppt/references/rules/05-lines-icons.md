# 05 — Lines & icons

**Category tag:** `lines`  
**When to update:** wrong stroke weight, straight vs curve, arrow AutoShapes, ungrouped pill icons, connectors inside icon groups.

## Law

> Stroke weight is **per role**. Connector path follows the photo (straight / elbow / curve).  
> Arrowheads are Line Begin/End Arrow — never arrow AutoShapes.  
> Composite icons = **one top-level group**; connectors stay outside.  
> **Every connector is a PPT Line** with two first-class properties: **arrow** and **curve** (`kind`).

## Line = connector with arrow + curve properties — UNIVERSAL

PowerPoint Format Shape → **Line** exposes Begin/End Arrow and the connector type.
Rebuilds must use the same object model — not rectangles, not Arrow AutoShapes.

| Photo shows | Set on the Line |
|-------------|-----------------|
| Straight spoke | `kind="straight"` |
| Sharp orthog. bend | `kind="elbow"` |
| Rounded bracket / smooth bend | `kind="curve"` |
| Arrowhead at tip | `end_arrow="triangle"` or `"open"` (V) |
| Arrowhead at start | `begin_arrow=…` |

```python
add_line(..., kind="curve", end_arrow="open", arrow_size="sm")
# 1→N bracket fan (middle straight, outer curves, arrow on every tip):
fan_out_lines(slide, origin_xy, target_xys, kind="curve", mid_kind="straight",
              end_arrow="open", color=..., width=...)
```

### Forbidden

| Anti-pattern | Do instead |
|--------------|------------|
| Diagonal + horizontal **segments** faking a bend | One `kind="curve"` / `elbow` connector |
| `MSO_SHAPE.RIGHT_ARROW` / chevron as the connector | Line + `end_arrow` |
| Curve in photo but `kind="straight"` elbows | Match photo → `curve` or `elbow` |
| Fan tips with no arrow when photo has them | `end_arrow` on **each** spoke |

## Progress / scrubber / meter (overlapping layers)

Many UI bars are **two shapes stacked**, not one:

1. **Back:** full-length **track** (light grey) spanning the whole control (or each segment’s full width).
2. **Front:** shorter **fill** (black / accent) on top covering only the completed portion.

Segmented steppers (Airbnb-style): grey track **per segment**, black fill on top (full or partial). White gaps between segments stay empty — do not invent a continuous black bar.

| Anti-pattern | Do instead |
|--------------|------------|
| Only draw the black chunks | Track (back) + fill (front) |
| Treat grey remainder as a separate unrelated bar | Same track role; fill ends where black ends |
| One shape with gradient faking fill|fill | Two solid shapes, z-order track then fill |

## Strokes

1. Measure px on the photo → `stroke_px_to_pt(stroke_px, img_h)`.
2. Prefer a real PPT **Line** (Format Shape → Weight: ¼ / ½ / ¾ / 1 / 1½ / … pt). Snap measured pt to the nearest menu value for hairline UI rules (1px photo ≈ ¾ pt here).
3. Do **not** fake thin rules with filled rectangles — they render heavier than Line Weight.
4. Roles differ: pill outline ≠ gray track ≠ mesh ≠ header rule. Do not reuse one weight for all lines.

## Composite controls (slider / crosshair marker) — UNIVERSAL

A selected slider / crosshair marker is **three stacked shapes**, never one oval:

| Role | Geometry | Color | Notes |
|------|----------|-------|-------|
| 1. Track | horizontal line | **grey** | thicker stroke; often one shared line for the whole slider |
| 2. Stem | vertical line | **same grey family as track** | thinner; rises from (or through) the track |
| 3. Circle | oval at intersection | **accent** (blue/green/…) | centered on track; sits on top |

### Detect automatically

```bash
python3 scripts/detect_stacked_marker.py \
  --image screenshot.png \
  --roi "cx-30,track_y-20,60,50" \
  --out work/marker.json
```

Use `roles.track|stem|circle` for colors + `stroke_px` / `diameter_px`. Build with:

```python
from helpers import add_crosshair_marker, stroke_px_to_pt
# draw shared track once, then:
add_crosshair_marker(
    slide, cx_in=..., track_y_in=..., stem_top_in=...,
    thumb_d_in=..., track_color=track_hex, stem_color=track_hex,  # stem = grey
    circle_color=accent_hex, track_pt=..., stem_pt=...,
)
```

### Forbidden

| Anti-pattern | Do instead |
|--------------|------------|
| One blue oval only | Track + stem + circle |
| Blue / accent-colored stem | Stem = track grey |
| Stem + circle ungrouped when they move as one | `group_shapes([stem, thumb])` |
| Guess stem weight | `detect_stacked_marker` / measure px → `stroke_px_to_pt` |

### Substring underline (related composite)

A highlight under one word (e.g. “intermediate”) is a **separate rectangle**, length = that word’s ink bbox (flush to first/last glyph), not the full sentence width. Measure gap text→bar on the photo.

## Docking (no float / no pile-up)

Connectors terminate **on shape edges**, never at a shared interior center that every spoke reuses.

1. Endpoint = `point_on_edge(box, side, t)` — **on** the stroke, not short of it.
2. Match `t` to the photo (top dual-arrow → `t≈0`, bottom → `t≈1`, mid → `0.5`).
3. **Fan-out** (1→N): source edge → each target’s facing edge mid.
4. **Fan-in** (N→1): each source edge mid → **staggered** `t` on the target edge via `edge_attach_ts(n)`. Never attach all N lines to the same mid-point (looks like one thick overlapping bundle).
5. Prefer `connect_shapes` / `connect_lr` when only one spoke per site; for multi-spoke fan-in use free lines with staggered edge points.
6. Elbow / L paths: bend at measured corner; tip still on the target edge (not through the fill).
7. After export, check the crop: **no gap** between tip and stroke. If PPT shortens the shaft oddly, nudge the endpoint 1px into the fill — never leave a visible air gap.
8. Forbidden: ending in empty space “near” the box; guessing `box.x - 10`.

## Text between parallel lines (corridor)

1. Measure both lines (or edges) as bounds.
2. Measure ink `w`/`h`.
3. If the photo (or user) wants **equal** gaps: `text_in_corridor(..., equal_gaps=True)`.
4. If gaps are intentionally asymmetric: pass measured `gap_left`/`gap_right`.
5. Forbidden: unequal side gaps when the photo is optically centered; stretching the placeholder until it hits a line.

## Paths

| Photo | Implementation |
|-------|----------------|
| Straight | `add_line(..., kind="straight")` |
| Elbow / L (sharp) | `kind="elbow"` or two segments only if photo is literally two strokes |
| Rounded bracket / smooth fan | `kind="curve"` + `fan_out_lines` |
| Arrow at tip | Always `end_arrow=` on that same Line |

## Arrows

- `end_arrow="triangle"` / `"open"` (or begin) on the **line** — never a separate arrow shape
- Size from photo (`sm` / `med`)
- Tip that visually touches a shape → endpoint on that edge
- Fan-out: **every** spoke gets the arrow property if the photo shows tips on each target

## Icons / composites

1. Capsule + two dots → `add_pill_icon` → top-level group.
2. 3D agent = back plate + front label → group as one unit when reusable.
3. Never nest card groups in a way that causes `DOUBLE_OFFSET_BUG` (`group_shapes` local coords).

## Mesh / many connectors

Internal mesh lines (workspace agents) use the lighter role weight; keep endpoints at shape **edge** centers unless the photo shows corner joins. Same docking law as fans.

## Gate

`verify_pptx` groups + `coord_mode: local`; `compare_render` catches origin-stacked groups. After export, **read** `compare/compare_side_by_side.png` for connector pile-up / gap drift even when card IoU passes.
