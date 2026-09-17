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
3. **Shadow (universal):** default = none (`disable_shadow` on every shape). If the photo (or a Format → Shadow panel crop) shows a soft drop shadow, map **every** panel field — do not guess blur/alpha:

| Panel field | `add_shadow` kwarg | Notes |
|-------------|--------------------|-------|
| Transparency % | `transparency_pct` | 18% → opacity 82% |
| Size % | `size_pct` | e.g. 101 → `sx`/`sy` 101000 |
| Blur pt | `blur_pt` | e.g. 11 |
| Angle ° | `dir_angle` | 90 = straight down |
| Distance pt | `dist_pt` | e.g. 4 |
| Color | `base` | sample gray bar / `#666666` |

```python
add_shadow(tile, blur_pt=11, dist_pt=4, transparency_pct=18,
           size_pct=101, dir_angle=90, base="#666666")
```

No panel? Fall back to `methodology.md` blur/dist/alpha tables — still never leave python-pptx’s default shadow.

## Forbidden

| Anti-pattern | Do instead |
|--------------|------------|
| Octagon “close enough” for a circle | `OVAL` |
| Drop 3D extrusion | Back+front plates, grouped |
| Huge fan that covers labels | Measured wedge bbox |
| Ignore radius | Sample / classify `rad` |
| Guess shadow blur/alpha | Read panel → `blur_pt` / `size_pct` / `transparency_pct` / `dist_pt` / `dir_angle` |
| Leave default python-pptx shadow | `disable_shadow` unless Pass B / panel says yes |

## Gate

`verify_pptx.py` → `gates.shape` (type, radius, position when declared).
