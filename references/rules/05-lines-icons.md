# 05 — Lines & icons

**Category tag:** `lines`  
**When to update:** wrong stroke weight, straight vs curve, arrow AutoShapes, ungrouped pill icons, connectors inside icon groups.

## Law

> Stroke weight is **per role**. Connector path follows the photo (straight / elbow / curve).  
> Arrowheads are Line Begin/End Arrow — never arrow AutoShapes.  
> Composite icons = **one top-level group**; connectors stay outside.

## Strokes

1. Measure px on the photo → `stroke_px_to_pt`.
2. Roles differ: pill outline ≠ gray mesh ≠ header rule.
3. Do not reuse one weight for all lines.

## Paths

| Photo | Implementation |
|-------|----------------|
| Straight | `add_line` |
| Elbow / L | Two segments or connector |
| Curve / fan | Curve / multiple lines matching photo |

## Arrows

- `end_arrow="triangle"` (or begin) on the **line**
- Size from photo (`sm` / `med`)
- Tip that visually touches a shape → endpoint on that edge

## Icons / composites

1. Capsule + two dots → `add_pill_icon` → top-level group.
2. 3D agent = back plate + front label → group as one unit when reusable.
3. Never nest card groups in a way that causes `DOUBLE_OFFSET_BUG` (`group_shapes` local coords).

## Mesh / many connectors

Internal mesh lines (workspace agents) use the lighter role weight; keep endpoints at shape centers unless the photo shows edge joins.

## Gate

`verify_pptx` groups + `coord_mode: local`; `compare_render` catches origin-stacked groups.
