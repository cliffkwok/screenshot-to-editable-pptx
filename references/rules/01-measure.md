# 01 — Measure

**Category tag:** `measure`  
**When to update:** wrong gaps, glued fans, centered leftover space, unequal sibling cards treated as equal, caption stretched into empty band.

## Law

> Measure every element against its neighbors (up / down / left / right).  
> Position = f(those distances).  
> **Nothing** is placed by leftover space, eyeballing, or “center in the remaining box.”  
> **Text size is measured too** — each label’s own cap-height → `font_pt_from_glyph` (see [04-text.md](04-text.md)). Do not reuse another element’s pt.  
> **Text↔text gaps are measured too** — every pair of neighboring text runs (stacked or inline) gets its own `gap_px` from ink boxes. See [04-text.md](04-text.md).  
> **Overlay badges** (circle on rect corner): measure badge center vs host top/right edges; two shapes, docked — never merge into one.  
> **No guessing:** if a pad / color / gap / pt cannot be read from the screenshot, **ask** — do not invent.  
> **Re-measure every element vs neighbors** — not only nest host pads. Inside a shape (badge → dashed lines, icon → caption, title → rule) each gap is its own measurement. Guessed fractions of parent `h`/`w` are forbidden.

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
7. Diagram frames may be **tan/gray**, not the header hue — `find_diagram_best` tries header stroke then `is_frame_stroke`.
8. Layouts without solid header bars (Pros/Cons, stroked containers) use `layout_kind=stroke_card`.
9. Flow / marketing / UI shots with no nestable cards → **SKIP** (not FAIL).
10. After changing `nest_detect.py`, run:
    `python3 scripts/eagle_batch_selftest.py`  
    (default: Eagle `Master Layout.library`). Expect `fail=0`.

## Sibling gaps inside a nest

Repeated rows / columns (agents, solution docs, …) use **measured** `h` + **uniform** `vgap` / `hgap` from the photo (`uniform_stack` / `nested_row_from_pads`). Do not invent taller boxes that compress the remaining rows.

Widen-for-one-line must **stop before the next sibling** (`max_right=` / parent clamp). Eating the measured gap is how connectors look “glued” or overlapping.

### Nested row pack (dashed host + N equal children)

Do **not** guess padding inside a stroked/dashed host:

1. Measure **child bodies** first (vertical stroke runs; AA thr often ~170).
2. Measure **host top/bottom** from horizontal dashed envelopes; bottom = last wide span **below labels** (labels belong inside the host).
3. Measure **host L/R** from **vertical dashed columns** outside the body cluster — **not** from the top horizontal span’s min/max x (rounded corners clip that span inward and fake `pad_L/R ≈ 0–2` when the eye sees ~15–20px).
4. Record `pad_L/T/R/B` via `pads_in_parent`, plus uniform `body_w` / `body_h` / `hgap`.
5. Place with `nested_row_from_pads` — rebuild err must be ≤ 2px vs measured bodies.
6. Overlay badges: if the circle sits **fully inside** the body, use `badge_inside_body_top` + measured `badge_pad_T`. Only use `badge_on_body_top` when the photo docks the badge on the top edge.
7. **Inner content under badge** (dashed “text” lines, glyphs, …): measure `badge_to_line0` and each line’s `y` (or `line_y_fracs`) — never invent `(0.38, 0.52, …)` of body height. Count lines from the photo (here: **3**, not 4).
8. **Labels under children:** ink-sized placeholder + measured `label_gap` from body bottom — **never** set label `h = pad_B` (stretches text into the bottom border and leaves empty top).
9. `assert_children_inside(host, children)` before grouping.
10. Also record pads vs **full content** (badge top → label bottom); `pad_T`/`pad_B` to content should match the photo (±2px).

Tool: `scripts/measure_nested_pack.py --image … --region x0,y0,x1,y1 --overlay nest.png`.

## Overlay badges (circle on rect)

Two shapes, not one merged control:

1. Measure **host** box and **badge** box independently.
2. Record `badge_cy - host_top` and `host_right - badge_cx` (or left). Typical: `cy ≈ host_top` (bisected by the top edge) **or** fully inside with `badge_pad_T > 0`.
3. Place badge from those distances; draw **host first**, badge **on top** (z-order).
4. Diameter ≈ measured badge ink; do not scale off host width by guess.

Helpers: `uniform_stack`, `assert_min_gap`, `pads_in_parent`, `nested_row_from_pads`, `badge_inside_body_top`, `badge_on_body_top`.

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

`caption_band_box`, `inset_box`, `abs_in_parent`, `pads_in_parent`, `nested_row_from_pads`, `badge_on_body_top`, `assert_children_inside`, `uniform_stack`, `assert_min_gap`, `point_on_edge`, `edge_attach_ts`, `label_above` / `label_below` — `scripts/helpers.py`.  
Nested pack detector: `scripts/measure_nested_pack.py`.
