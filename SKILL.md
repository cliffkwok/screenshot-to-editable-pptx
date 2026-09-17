---
name: screenshot-to-editable-ppt
description: Rebuild a screenshot as native editable PowerPoint using shapes, text, and grouped icons — not a pasted image. Use when the user gives a slide screenshot, Fit-to-Window capture, or asks to replicate layout, shape, font, color, or shape-combinations into .pptx. Must pass source_audit.py (spec vs original), verify_pptx.py (shape/font/color), and compare_render.py (PowerPoint raster vs original) before delivery.
---

# Screenshot to Editable PPT

Rebuild a slide screenshot as object-level editable PowerPoint. Native shapes, real text, grouped so it scales. Never wrap the screenshot as a picture.

Future inputs will vary (different decks, icons, layouts) but the job is always the same: **layout, shape, font, color, and combinations of shapes**. Do not replicate the screenshot as an image. Reconstruct icons from native shapes and group them in a meaningful order (one group per component: card, icon, badge).

Verbatim delivery contract:

> I want to make a screenshot and then have it become an editable PowerPoint. I need it to be 100% accurate, so the shape, font, and color will all be checked before sending it to me.

## Hard rule — do not send on fail

Do **not** give the user a `.pptx` path, open the file, or say the work is done until:

0. **[Pre-delivery checklist](references/pre-delivery-checklist.md)** — every **category** ticked (`measure` / `color` / `shape` / `text` / `lines` / `delivery`)
1. `source_audit.py` exits 0 — spec text boxes contain ink on the **original screenshot**, glyph height matches declared pt, boxes overlap measured lines
2. `verify_pptx.py` exits 0 with `gates.shape`, `gates.font`, `gates.color` all true
3. `compare_render.py` exits 0 — a **real PowerPoint slideshow raster** vs the original screenshot (card IoU, no origin-stacked groups, highlight not covering extra glyphs)

**Order:** finish the rebuild → run checklist A → run gates B → only then deliver (statement C). Skipping the checklist is a fail even if gates pass.

## Rule categories (learn once → apply forever)

Corrections are filed by category so you only re-teach one slice:

| Tag | File |
|-----|------|
| index | [references/rules/README.md](references/rules/README.md) |
| `measure` | [references/rules/01-measure.md](references/rules/01-measure.md) |
| `color` | [references/rules/02-color.md](references/rules/02-color.md) |
| `shape` | [references/rules/03-shape.md](references/rules/03-shape.md) |
| `text` | [references/rules/04-text.md](references/rules/04-text.md) |
| `lines` | [references/rules/05-lines-icons.md](references/rules/05-lines-icons.md) |
| `delivery` | [references/rules/06-delivery.md](references/rules/06-delivery.md) |
| log | [references/rules/LEARNINGS.md](references/rules/LEARNINGS.md) |

**When you correct something:** agent appends `LEARNINGS.md` with the category tag, promotes the reusable line into that category file, and re-runs the checklist. You should not need to repeat it on the next screenshot.

Pointer index (same law): [references/universal-measure-rule.md](references/universal-measure-rule.md).

One-line law: **measure every element against its neighbors (up/down/left/right); never place by leftover space.**

Must-do when creating the slide (by category):

1. **Measure / nest** → run `scripts/nest_detect.py --self-test`; place from `pads_in_parent` (card→header→diagram→caption).
2. **Text** → ink↔shape pads; wrap from photo; mid-word wraps = defects (widen).
3. **Shape** → correct primitive (ellipse→oval); 3D = back+front.
4. **Color** → PIL sample + `color_probes`.
5. **Lines** → stroke per role; Line arrows; top-level icon groups.
6. **Delivery** → checklist + three gates before any path to you.

When the user corrects one instance, **propagate to every similar element** and update the matching category file + `LEARNINGS.md`.

```bash
python3 scripts/text_hints.py \
  --image <screenshot.png> \
  --out <work/text_hints.json> \
  --overlay <work/text_hints.png>

python3 scripts/source_audit.py \
  --spec <work/spec.json> \
  --original <screenshot.png> \
  --hints <work/text_hints.json> \
  --out <work/source_audit.json>

python3 scripts/verify_pptx.py \
  --pptx <out.pptx> \
  --spec <work/spec.json> \
  --original <screenshot.png> \
  --out <work/verify_report.json>

python3 scripts/export_slide_png.py \
  --pptx <out.pptx> \
  --out <work/render.png>

python3 scripts/compare_render.py \
  --original <screenshot.png> \
  --render <work/render.png> \
  --out <work/compare>
```

On fail: fix every listed item, rebuild, re-export, re-compare. Repeat until all three pass. The user is not QC. XML inspect that looks correct while PowerPoint parks a card top-left is still a fail. `verify_pptx` matching a guessed spec is not enough — `source_audit` must pass against the photo.

## Workflow

Copy this checklist and keep it updated:

```
- [ ] 1. Analyze screenshot (elements, z-order, shadows, text lines, icon sub-shapes)
- [ ] 2. PIL-sample colors into work/colors.json
- [ ] 3. Measure boxes as % of a container → work/proportions.json
- [ ] 3b. python3 scripts/text_hints.py → work/text_hints.json (glyph boxes + pt)
- [ ] 4. Write work/spec.json (one text element per visual line; font_size_source=measured)
- [ ] 5. Build native PPTX with scripts/helpers.py (add_line_text / add_text_from_hint)
- [ ] 6. python3 scripts/pptx_inspect.py --pptx out.pptx --out work/inspect.json
- [ ] 6b. python3 scripts/source_audit.py ...  (must pass vs original)
- [ ] 7. python3 scripts/verify_pptx.py ...  (must pass)
- [ ] 8. Confirm inspect groups have `"coord_mode": "local"` (not DOUBLE_OFFSET_BUG)
- [ ] 9. python3 scripts/export_slide_png.py && python3 scripts/compare_render.py
- [ ] 10. Deliver path + reports only after steps 6b–9 pass
```

### 1. Analyze

Vision, two passes:

- Pass A: list every visible element, relative position %, z-order.
- Pass B: per element — shape type, corner radius class, fill vs outline, shadow yes/no, text line count, font weight.

Do not guess hex. Do not guess inches. Do not guess point size.

### 2. Color (PIL only)

```bash
python3 scripts/pil_sampler.py \
  --image screenshot.png \
  --coords "(x,y) (x2,y2)" \
  --regions "card:x,y,w,h header:x,y,w,h" \
  --out work/colors.json
```

Sample the **center** of a solid fill, not the edge. If the sample is unexpectedly white, offset ±5px and retry. Put those hex values and pixel coords into `spec.json` `color_probes` so verify can re-sample the original.

### 3. Measure (proportion chain)

Pick one container (usually the main card or the slide). Express every element as % of that container:

```
x% = (el_x - c_x) / c_w × 100
```

```bash
python3 scripts/proportion_chain.py \
  --container-box "x,y,w,h" \
  --container-inch "13.33,7.5" \
  --elements "title:x,y,w,h icon:x,y,w,h" \
  --out work/proportions.json
```

Absolute PPT inches = percentage × container inches.

### 3b. Glyph-box font size (do not guess pt)

```bash
python3 scripts/text_hints.py \
  --image screenshot.png \
  --out work/text_hints.json \
  --overlay work/text_hints.png \
  --slide-h 7.5 --lang eng+chi_tra

python3 scripts/text_measure.py \
  --image screenshot.png \
  --spec work/spec.json \
  --out work/text_measure.json
```

Each detected line is an ink-tight `box_px` plus `glyph_height_px`. Point size is:

```
latin_pt = glyph_h_px / img_h × slide_h_in × 72 / 0.72
cjk_pt   = glyph_h_px / img_h × slide_h_in × 72 / 0.88
```

Same-height lines share one `size_group` and one locked pt (`size_group_font_pt_latin` / `_cjk`). Copy that into spec — never invent 38/16/11.

**Two text modes:**
1. **Measured single line** (`add_line_text`, `wrap=False`): titles, node labels — one box per visual line, box = ink + pad.
2. **Placeholder flow** (`add_flow_text` / `caption_band_box` + `wrap=True`): captions that wrap — **one** text box. **Measure padding to the shape above and the element below**; that sets the placeholder’s `y`/`h`. Measure width so line breaks match the photo; set `align` (center/left) from the source. Never stretch the box into empty leftover space.

**Flowing shapes (same distance rule):** arrows, fans, capsules, and divider lines are placed by measuring gap to the upside element (title placeholder / rule / parent border) and to siblings / card edges. If a rule touches the card L/R in the screenshot, draw it full-width. Do not evenly pack leftover body space. For arrow+capsule stacks, measure the **flow group** bbox (L/R/T/B vs card) and keep **arrow lengths** equal to the original.

**Bold is measured, not assumed.** `text_measure.py` compares stroke stem width to glyph height (Arial regular ≈ 0.10–0.15 em, bold ≈ 0.20+). White-on-color headers and small captions default to regular — do not set `bold=True` unless measure says so.

**Position loop:** after the first PowerPoint raster, run `text_fit.py` (original vs render ink centroids → `dx_px` / `dy_px` / optional pt scale), rebuild, re-audit.

### 4. Write spec.json

Follow [references/spec-schema.md](references/spec-schema.md). Every visible element needs:

- shape type + position/size %
- fill/line hex from PIL
- for text: exact string, font name, **measured** pt (`font_size_source: "measured"`), bold, color, alignment, optional `box_px` / `glyph_height_px` / `size_group`
- `source: {width_px, height_px, fit}` so source-audit can map % → screenshot pixels

`verify_pptx.py` fails closed if spec is incomplete. `source_audit.py` fails closed if a text box has no ink on the original, glyph height is off, or the box misses a measured line.

### 5. Build

16:9 default: 13.33" × 7.5". Blank layout. Import helpers:

```python
from helpers import new_presentation, add_shape, add_text, add_line_text, add_text_from_hint, add_shadow, group_shapes, disable_shadow
```

Build bottom → top: background, containers, diagrams/icons, text, overlays. Then group related shapes. Flattened ungrouped output is a fail.

Details: [references/python-pptx.md](references/python-pptx.md) and [references/methodology.md](references/methodology.md).

Rules that caused past misses:

- `disable_shadow(shape)` on every shape. Only call `add_shadow` when Pass B said yes.
- Rounded rect `adjustments[0]`: 0.03–0.08 small, 0.15–0.25 large, **0.5 = pill**.
- Circle = `OVAL` with width == height.
- Diagram spines use `connect_lr` / `connect_shapes` / `add_line`. **Arrows are line properties** (`end_arrow="triangle"` → PowerPoint Line → End Arrow), never `RIGHT_ARROW` shapes. Measure stroke px → pt (`stroke_px_to_pt`). **Outline weight ≠ connector weight** — a pill/capsule outline is often 2–3× heavier than the gray arrow line; measure each role separately. **Connector shape:** detect straight vs elbow (sharp corners) vs **curve** (smooth arcs) from the photo — Parallel fan-in/out is usually `kind="curve"`, not elbow.
- Icons are often several shapes. Do not fake them with one shape or a letter unless the source is that simple. **Capsule + two dots (or any shell + inner marks) → one group** (`add_pill_icon` / `group_shapes`). That icon group must stay **top-level** — do not nest it inside the card group, or PowerPoint click-selects the inner rounded rect (yellow radius handle) instead of the group. Connectors stay outside the icon group.
- **Text boxes:** measured single-line labels use `wrap=False` (one box per line). Captions that wrap in the photo use **one placeholder** with `wrap=True` (`add_flow_text`) so text flows to the next line — do not stack fake line boxes.
- **One visual line = one text box** for measured labels only, `wrap=False`. Size from measured ink (`pad_ink_box_px`). After a first PowerPoint raster, `text_fit.py` nudges `dx/dy` and pt from original vs render ink.
- No raster pictures unless the screenshot actually contains a photo.
- **Groups:** never assign `shape.left` / `shape.top` after a shape is inside `p:grpSp`. Snapshot EMUs, move the XML nodes, write **local** `a:off`, set `chOff` to `(0,0)`. Double-offset (`chOff = min_x` AND children already subtracted) makes PowerPoint park the group at the slide origin. `python-pptx` `.left` will still look correct — verify must use the OOXML formula `off + (childOff - chOff)`. A card that jumps to the top-left is this bug, not a layout choice.
- **Glyph highlights:** a marker behind part of a title is not a second screenshot rectangle. Screenshot gold blobs pick up proofing squiggles and JPEG fringe and come out ~2× too wide. Lock the bar to the substring: CJK advance = 1em at the title size, title centered, `index × em`. Width = `len(substring) × em` plus a few px pad. Use `cjk_centered_substring_box`.
- **Container padding:** every card/header/diagram/caption is a parent box. **Measure each container’s pixel box** — sibling cards can differ in height/width. Measure inset from parent edge to children and gaps between siblings. Text *on* a filled shape → shape text frame (`set_shape_text`). **Measure text↔shape gap on the screenshot** (`measure_text_in_shape` → `pad_frac` + glyph pt); `font_pt_fit_shape` caps so ink keeps that breathing room. Never let header/LLM text run edge-to-edge in a circle. Free labels near nodes stay `label_above` / `label_below`.
- **Nested group children (critical):** before `group_shapes`, every child of a card/diagram must fit inside its parent nest. Lay out in **parent-local** coords (`abs_in_parent`), never invent a child taller/wider than the nest box (classic fail: workspace taller than the diagram → Agents/Synthesizer pile when the group is selected). Call `assert_children_inside(parent_box, [{name, box_px}, …])` as a hard gate. Widen-for-one-line labels must clamp to the parent right edge (`parent_box=`). Run `scripts/nest_detect.py --self-test` and use measured `pads_in_parent` — details in [references/rules/01-measure.md](references/rules/01-measure.md).
- **Sibling gaps + connector docking:** repeated rows use measured `h` + uniform `vgap`/`hgap` (`uniform_stack`, `assert_min_gap`). Connectors end on **edges** (`point_on_edge`); fan-in uses staggered `edge_attach_ts(n)` — never attach N spokes to one mid-point (overlapping bundle). See [05-lines-icons.md](references/rules/05-lines-icons.md).
- **Auto compare→learn:** after every rebuild, export + `compare_render`, **read** the side-by-side, fix remaining visual defects, append `LEARNINGS.md`, promote into `01`–`06` — without waiting for the user to say “encode this” ([06-delivery.md](references/rules/06-delivery.md) §D).

### 6. Inspect, then verify

```bash
python3 scripts/pptx_inspect.py --pptx out.pptx --out work/inspect.json
python3 scripts/source_audit.py \
  --spec work/spec.json --original screenshot.png \
  --hints work/text_hints.json --out work/source_audit.json
python3 scripts/verify_pptx.py \
  --pptx out.pptx \
  --spec work/spec.json \
  --original screenshot.png \
  --out work/verify_report.json
python3 scripts/export_slide_png.py --pptx out.pptx --out work/render.png
python3 scripts/compare_render.py \
  --original screenshot.png --render work/render.png --out work/compare
```

| Gate | Passes when |
|------|-------------|
| **source** | Each spec text box has ink on the original; glyph height matches declared pt (ratio 0.75–1.35); box overlaps a `text_hints` line (IoU ≥ 0.15). |
| **color** | Each `color_probes` hex matches the original image at those pixels (±2 RGB), and the matching PPT shape uses that hex (±2 RGB). |
| **font** | Each spec text run is found; name, size (±1 pt), bold, and text color match. |
| **shape** | Type, radius class, circle constraint, position/size (±3% of slide), grouping, and no unexpected pictures. |
| **visual** | PowerPoint slideshow raster vs original: card count matches, min card IoU ≥ 0.70, no group parked at the origin, highlight not covering extra glyphs. |

Exit code 1 → do not deliver. Quick Look is not a valid visual.

### 7. Deliver

After all three pass:

- `.pptx` path
- `source_audit.json` top-level `passed: true`
- `verify_report.json` top-level `passed: true`
- `compare/compare_report.json` top-level `passed: true`
- note any recorded warnings (warnings do not block; gate failures do)

## After ANY modification (re-verify)

Borrowed from the same fail-closed habit used by polished slide skills: **edits do not skip gates**.

After you change layout, text, connectors, grouping, fonts, or colors:

1. Rebuild the `.pptx`
2. Re-run `source_audit.py`
3. Re-run `verify_pptx.py`
4. Re-export with `export_slide_png.py` (real PowerPoint slideshow raster)
5. Re-run `compare_render.py`

Do not hand-wave from XML inspect alone. PowerPoint draw position can still be wrong when the XML “looks right.”

## Fixed stage invariant

Treat the rebuild canvas as a **fixed 16:9 stage**:

- Default slide size: **13.333 in × 7.5 in** (widescreen / Fit-to-Window)
- Measure everything as % of that stage (or of one chosen container), never freehand inches
- Compare original vs render at the **same aspect ratio** — do not stretch one side to force a match
- Fit-to-Window captures are proportion targets, not pixel-identity targets

## Progressive disclosure (load on demand)

Keep `SKILL.md` as the map. Load supporting files only when the current step needs them:

| File | Purpose | Load when |
|------|---------|-----------|
| `SKILL.md` | Workflow + hard gates | Always |
| `scripts/text_hints.py` | Per-line ink boxes + glyph→pt | Before writing text into spec |
| `scripts/text_measure.py` | Bold/weight + centroid | When weight or fine position is unsure |
| `scripts/text_fit.py` | Original vs render ink deltas | After a render, if size/pos still drift |
| `scripts/source_audit.py` | Spec vs original photo | Before claiming layout is locked |
| `scripts/verify_pptx.py` | Shape / font / color gates | Before visual compare |
| `scripts/export_slide_png.py` + `compare_render.py` | Real PPT raster vs photo | Before delivery |
| `scripts/helpers.py` | Builders, groups, connectors | While building |
| `references/spec-schema.md` | Spec field contract | When writing / editing `spec.json` |
| `references/methodology.md` | Measurement detail + anti-patterns | When stuck on accuracy |
| `references/python-pptx.md` | OOXML grouping / text gotchas | When grouping or text XML fails |
| `examples/walkthrough.md` | End-to-end example | First time / onboarding |

## What this is not

- Not a pasted full-slide screenshot inside PPT.
- Not HTML / web decks (different problem than [frontend-slides](https://github.com/zarazhangrui/frontend-slides)).
- Not authoring a new presentation from a written brief (no source image).

## Dependencies

```bash
pip3 install -r requirements.txt
```

`python-pptx`, `Pillow`, `lxml`. `text_hints.py` uses the `tesseract` CLI (`eng+chi_tra`) when installed; glyph boxes still refine to ink pixels. Visual compare needs Microsoft PowerPoint on macOS.
