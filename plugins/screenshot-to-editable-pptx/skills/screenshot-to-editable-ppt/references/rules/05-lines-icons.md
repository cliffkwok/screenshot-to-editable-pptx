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

## Docking (no float / no pile-up)

Connectors terminate **on shape edges**, never at a shared interior center that every spoke reuses.

1. Use `point_on_edge(box, side, t)` for endpoints (`t=0.5` = mid).
2. **Fan-out** (1→N): source edge → each target’s facing edge mid.
3. **Fan-in** (N→1): each source edge mid → **staggered** `t` on the target edge via `edge_attach_ts(n)`. Never attach all N lines to the same mid-point (looks like one thick overlapping bundle).
4. Prefer `connect_shapes` / `connect_lr` when only one spoke per site; for multi-spoke fan-in use free lines with staggered edge points.
5. Elbow / L paths: bend at measured corner; tip still on the target edge (not through the fill).

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

Internal mesh lines (workspace agents) use the lighter role weight; keep endpoints at shape **edge** centers unless the photo shows corner joins. Same docking law as fans.

## Gate

`verify_pptx` groups + `coord_mode: local`; `compare_render` catches origin-stacked groups. After export, **read** `compare/compare_side_by_side.png` for connector pile-up / gap drift even when card IoU passes.
