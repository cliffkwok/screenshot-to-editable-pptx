# 03 — Shape

**Category tag:** `shape`  
**When to update:** wrong primitive (octagon for ellipse), flat box instead of 3D block, corner radius, overlap, missing dog-ear / wedge.

## Law

> Match the **photo’s geometry class**, not a convenient approximation.  
> Measure `w×h`, corner radius class, and z-order. No overlaps the photo does not show.

## Geometry class map

| Photo shows | Use | Do **not** use |
|-------------|-----|----------------|
| Smooth ellipse / circle outline | `OVAL` | `OCTAGON`, polygon approx |
| Rounded rect process box | `ROUNDED_RECTANGLE` + measured `rad` | Sharp rect if photo is rounded |
| 3D block / isometric cube | Back plate offset + front face (group) | Single flat rect |
| Document with folded corner | Rect + small triangle overlay | Plain rect only |
| Fan / wedge into a node | Triangle / freeform matching photo | Oversized overlapping triangle |

## Size & overlap

1. Box `w×h` from photo ink (or host), not “what fits the leftover”.
2. If widening for single-line text (see **Text**), grow the box; do not crush neighbors — re-measure `gap` after widen.
3. No accidental overlap (Coordinator through Workspace ring, Synthesizer over fan, …) unless the photo shows it.

## Cards / chrome

1. Card body, header bar, diagram frame — each measured.
2. Header height from solid fill band (not including body content that shares a hue).
3. Shadow only if photo has it — read the shadow **panel** when available:
   `add_shadow(blur_pt=…, dist_pt=…, transparency_pct=…, size_pct=…, dir_angle=90, base="#666666")`.
   Example (soft icon tile): blur 11 pt, distance 4 pt, transparency 18%, size 101%, angle 90°.

## Forbidden

| Anti-pattern | Do instead |
|--------------|------------|
| Octagon “close enough” for a circle | `OVAL` |
| Drop 3D extrusion | Back+front plates, grouped |
| Huge fan that covers labels | Measured wedge bbox |
| Ignore radius | Sample / classify `rad` |

## Gate

`verify_pptx.py` → `gates.shape` (type, radius, position when declared).
