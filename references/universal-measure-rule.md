# Universal measure rule (every screenshot)

**Mandatory on every screenshot → editable PPT rebuild.** Not deck-specific.
When the user corrects one card or label, **apply the same rule to every similar element** without waiting to be told again.

Full skill entry: [../SKILL.md](../SKILL.md). Cursor short form: project rule `screenshot-to-editable-ppt`.

---

## Core law

> **Measure every element against its neighbors** (up / down / left / right).  
> Position = f(those distances).  
> **Nothing** is placed by leftover space, eyeballing, or “center in the remaining box.”

### Forbidden (caused repeated misses)

| Anti-pattern | Do instead |
|--------------|------------|
| Stretch text/diagram to fill leftover card space | Size from measured pads to neighbors |
| Center a diagram in leftover body when pads are unequal | Use measured `pad_T` / `pad_from_rule` / `pad_B` |
| Fix only the element the user pointed at | Fix **all** siblings with the same pattern |
| Inset a divider that touches the card L/R in the photo | Full parent width |
| Stretch arrow length to meet a shape | Measured shaft length (+ tip gap if photo has one) |
| Park a label on the wrong host | Host = the shape the label names in the photo |
| Default `gap=4` for `label_above` | Measured gap from ink ↔ host |
| Glue a fan to the divider when the photo has a top body gap | Preserve `pad_from_rule` (often ≈ header height) |
| Wrap a single-line label because the box was too narrow | `wrap=False`, width ≥ ink |
| Guess pt that fills a circle/bar | Measure ink↔edge `pad_frac`, cap with `font_pt_fit_shape` |

---

## Procedure (before writing coordinates)

For each visible element E:

1. Identify **host / neighbors**: parent, shape above/below/left/right, named host (labels).
2. Record pixel distances on the screenshot:
   - `pad_L/R/T/B` vs parent (or flow-group bbox vs card)
   - `gap` to each neighbor (label↔node, tip↔capsule, title↔rule, …)
   - Internal sizes: shaft length, pill `w×h`, gutters
3. Place E from those numbers only.
4. Shared patterns (N similar cards) → **measure each**; do not copy one card’s leftovers.

---

## 1. Containers

1. Measure each parent box (`x,y,w,h` in source px).
2. **Siblings are independent** — unequal widths/heights/gutters are normal.
3. Children are relative to that parent — never absolute slide guesses.

---

## 2. Text placeholders (captions / titles / callouts)

| Measure | Meaning |
|---------|---------|
| `pad_top` | Shape above → text ink top |
| `pad_bot` | Text ink bottom → shape/edge below |
| width / side | So line breaks match the photo |
| `align` | As in the source |

Helper: `caption_band_box`. Never expand into empty leftover space.

### 2b. Wrapping

From the **photo**, not a guessed width:

1. **One** visual line → `wrap=False`, box width ≥ ink (+ pad).
2. **Two+** lines in one band → `wrap=True`, one placeholder; width so breaks match.
3. Never fake stacked single-line boxes for a wrapped caption; never wrap a source single-line label.

---

## 3. Text vs shape (create-time, every slide)

### 3a. Text *inside* a filled shape (header bar, “LLM” in a circle)

1. Shape-native **Edit Text** (`set_shape_text` / `add_shape_with_text`).
2. Measure ink ↔ host on **all four sides** (T/B/L/R) → `pad_frac` / margins / glyph pt.
3. Cap pt with `font_pt_fit_shape(..., pad_frac=…)`.
4. After raster: confirm letters are not edge-to-edge and vertical balance matches the photo.

### 3b. Text *near* a shape (Input / Router / Intermediate…)

1. Correct **host** from the photo.
2. Measured gap; `label_above` / `label_below` (no default gap).
3. Align to host center or named segment.
4. Stacked labels on one host each get their own measured gap.

---

## 4. Dividers / rules

Photo shows L/R contact with the parent → **full parent width**. Do not apply content side-pad to the rule.

---

## 5. Flow groups vs surrounding space

When arrows + capsules / fans / loops read as one unit:

1. Treat as one **flow group** (conceptual or real PPT group).
2. Measure group bbox vs surrounding card:
   - `pad_L`, `pad_R`
   - `pad_from_rule` / `pad_T` — gap from divider to **first** group ink (fan origin or top shape); **often > 0**
   - `pad_B`
3. Place from those pads; internals from measured gaps/lengths.
4. Do **not** center in leftover body space when pads are unequal.
5. Do **not** glue a fan to the divider unless the photo shows that join.
6. Tip touches target in the photo → end connector on that edge.
7. Apply to **every** sibling card in the row.

---

## 6. Lines, icons, bold (always)

- Stroke weight **per role** (pill outline ≠ gray connector); `stroke_px_to_pt`.
- Connector geometry: straight / elbow / **curve** from the photo.
- Arrowheads = Line Begin/End Arrow — never arrow AutoShapes.
- Capsule + dots = **one top-level group** (`add_pill_icon`); connectors outside.
- Bold is measured (stem), not assumed.

---

## 7. Apply once → apply everywhere

On any spacing/padding/wrap/host correction:

1. State the universal rule in one line.
2. Fix **all** matching instances in this screenshot.
3. Update this file if a new reusable sub-case appears.

---

## 8. Pre-build checklist

- [ ] Each card/parent measured independently
- [ ] Titles/captions: pad upside + downside; wrap from photo
- [ ] In-shape text: T/B/L/R pad + pt (`pad_frac`)
- [ ] Near-shape labels: correct host + measured gap
- [ ] Dividers: full-width vs inset from photo
- [ ] Each diagram: flow-group L/R/`pad_from_rule`/B + internals
- [ ] Same pattern on all sibling cards
- [ ] Stroke per role; connector shape; top-level icon groups
- [ ] `source_audit` + `verify_pptx` + `compare_render` all pass

---

## Helpers

`caption_band_box`, `inset_box`, `measure_text_in_shape`, `font_pt_fit_shape`, `label_above` / `label_below`, `add_line` + `set_line_arrows`, `add_pill_icon`, `group_shapes` — `scripts/helpers.py`.
