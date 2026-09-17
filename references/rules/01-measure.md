# 01 — Measure

**Category tag:** `measure`  
**When to update:** wrong gaps, glued fans, centered leftover space, unequal sibling cards treated as equal, caption stretched into empty band.

## Law

> Measure every element against its neighbors (up / down / left / right).  
> Position = f(those distances).  
> **Nothing** is placed by leftover space, eyeballing, or “center in the remaining box.”

## Containers (box-inside-box)

1. Measure each parent box (`x,y,w,h` in source px) **independently**.
2. Sibling cards may differ in width / height / gutter — do not assume equality.
3. Children are relative to that parent — never absolute slide guesses.
4. **Nest hierarchy** (typical slide card):
   ```
   card
     ├─ header   (often flush top / full card width)
     ├─ diagram  (INNER stroked rect — inset → pad_L/R/T/B > 0)
     └─ caption  (band under diagram)
   ```
5. Run `scripts/nest_detect.py --image … --self-test` before placing children.  
   Use `pads_in_parent` from the JSON — do not invent equal insets.
6. Self-test rejects diagrams that are tiny inner widgets (`pad_L+pad_R` too large vs card width).

## Sibling gaps inside a nest

Repeated rows / columns (agents, solution docs, …) use **measured** `h` + **uniform** `vgap` / `hgap` from the photo (`uniform_stack`). Do not invent taller boxes that compress the remaining rows.

Widen-for-one-line must **stop before the next sibling** (`max_right=` / parent clamp). Eating the measured gap is how connectors look “glued” or overlapping.

Helpers: `uniform_stack`, `assert_min_gap`.

## Nested group children (critical)

When a card / diagram is grouped in PPT, **overflowing children look like piled / overlapping members** even if `group_shapes` used local `chOff=0`.

1. Lay out every child in **parent-local** coords (`abs_in_parent(parent, local_xywh)`).
2. Child size must fit the remaining parent space — never invent `h`/`w` larger than the nest box (classic fail: workspace taller than diagram).
3. Call `assert_children_inside(parent_box, [{name, box_px}, …])` **before** `group_shapes`.
4. Widening a label for one-line text must clamp to the parent right edge (`parent_box=`).
5. Mesh / connector endpoints: use absolute px from the layout math, not `shape.left` after nesting groups.
6. `group_shapes`: children local, `chOff=(0,0)` — never assign `.left/.top` after the node is inside `grpSp`.

## Pads (record on the photo)

| Token | Meaning |
|-------|---------|
| `pad_L` / `pad_R` / `pad_T` / `pad_B` | Element (or flow-group bbox) → parent edge |
| `pad_from_rule` | Divider / header bottom → **first** diagram ink (often > 0) |
| `gap` | Element ↔ named neighbor (label↔node, tip↔capsule, …) |

## Flow groups

When arrows + capsules / fans / loops read as one unit:

1. One **flow group** (conceptual or real PPT group).
2. Place from `pad_L/R`, `pad_from_rule` / `pad_T`, `pad_B` — not leftover fill.
3. Do **not** glue a fan to the divider unless the photo shows that join.
4. Tip touches target in the photo → end connector on that edge.
5. Apply to **every** sibling card.

## Dividers / rules

Photo shows L/R contact with the parent → **full parent width**. Do not apply content side-pad to the rule.

## Captions / placeholders

Use `caption_band_box(card, diagram, pad_top, pad_bot, side_pad)`. Never expand the placeholder into empty leftover space under the diagram.

## Forbidden

| Anti-pattern | Do instead |
|--------------|------------|
| Stretch diagram to fill leftover body | Size from measured pads |
| Center when `pad_T` ≠ `pad_B` | Use the measured pads |
| Copy one card’s leftovers to siblings | Measure each card |
| Inset a full-bleed divider | Full parent width |

## Helpers

`caption_band_box`, `inset_box`, `abs_in_parent`, `assert_children_inside`, `uniform_stack`, `assert_min_gap`, `point_on_edge`, `edge_attach_ts`, `label_above` / `label_below` — `scripts/helpers.py`.
