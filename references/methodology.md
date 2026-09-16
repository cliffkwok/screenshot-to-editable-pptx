# Exact reconstruction methodology

Rules that stop the usual failures: guessed hex, guessed inches, default shadows, overflow, overlap, ungrouped output.

## 1. Proportion chain

Never guess absolute values. Pick a container (main card or the slide).

```
element_x% = (element_x - container_x) / CONTAINER_W × 100
ppt_x      = container_x_in + element_x% × container_w_in / 100
```

Run `scripts/proportion_chain.py`. Put the resulting `slide_pct` values into `spec.json`.

Font size is **not** guessed from the proportion chain. Measure glyph height with `scripts/text_hints.py`, then lock same-height lines to one `size_group`.

## 2. PIL color

Vision hex is a guess. PIL at a fill center is the source of truth.

- Sample the interior, not the stroke.
- Thin borders: sample 2px outside, or skip and use interior fill.
- Unexpected `#FFFFFF` → offset ±5px (`pil_sampler.py` already retries).
- Record `{hex, sampled_at}` as a `color_probes` entry.

## 3. Shadows

Default is **no shadow**. python-pptx adds one unless `disable_shadow(shape)` runs on every shape.

Only call `add_shadow` when Pass B said that element has a shadow.

| Background | blurRad | dist | alpha | base |
|------------|---------|------|-------|------|
| Dark `#141414` | 80000 | 0 | 50000 | `000000` |
| Mid gray | 30000 | 10000 | 15000 | `000000` |
| Light `#F5F5F5` | 25000 | 8000 | 5000–8000 | `999999` |
| White card | 20000 | 6000 | 5000 | `999999` |

Light backgrounds: alpha ≤ 8000. Nearly invisible source shadow → 5000.

## 4. Shape types

| Source corner | MSO_SHAPE | `adjustments[0]` |
|---------------|-----------|------------------|
| square | RECTANGLE | — |
| slight round | ROUNDED_RECTANGLE | 0.03–0.08 |
| obvious round | ROUNDED_RECTANGLE | 0.15–0.25 |
| pill | ROUNDED_RECTANGLE | **0.5** |
| circle | OVAL | width == height |

When unsure, use the **smaller** radius. Over-rounding is obvious.

## 5. Icons

Close-up must answer: fill or outline; shape class; sub-element count; width / container width; each sub-element hex from PIL.

Build each sub-shape. Do not replace a composite icon with one shape or a letter unless the source is that simple.

**Composite glyph = one group.** If a rounded capsule (pill) contains two dots (or any shell + inner marks that read as one icon), build the shell and the dots as separate shapes, then **`group_shapes` them immediately**. Selecting that icon in PowerPoint must show **one** bounding box **with no yellow radius handle** (a radius handle means you selected the rounded rect, not the group). Keep the icon group **top-level on the slide** — nesting it inside a card group makes click-select hit the inner rect. Connectors stay outside the icon group. `group_shapes(..., nest_groups=False)` is the default.

Helper: `add_pill_icon` (rounded rect + two ovals → one group).

## 6. Text (glyph box + one box per line)

Do not guess pt. Do not size a box with `char_count × 0.6`.

```
latin_pt = glyph_h_px / img_h × slide_h_in × 72 / 0.72   # cap-height ≈ 0.72em
cjk_pt   = glyph_h_px / img_h × slide_h_in × 72 / 0.88
```

`scripts/text_hints.py` (Tesseract TSV → ink-refined box) writes `box_px`, `glyph_height_px`, `font_pt_if_latin` / `_cjk`, and a `size_group`. Same-level lines share the group's median pt. OCR strings can be dirty — Vision still owns the exact visible string; the hint owns the box and the pt.

Rules:

- **Measured labels** (titles, Input/Output): one visual line = one PowerPoint text box. `add_line_text` / `add_text_from_hint` set `wrap=False`.
- Box = tight ink + pad (`pad_ink_box_px`, ~0.14w / 0.20h of glyph height).
- Centered titles still use `align="center"` inside that padded ink box — do not stretch the box to the full card unless the source does.
- **Wrapped captions / paragraphs:** when the screenshot shows text flowing to the next line inside a band, use **one** text box with `wrap=True` (`add_flow_text` / `text_in_box(..., wrap=True)`). Size the box to the caption band; let PowerPoint wrap. Do not split into stacked single-line boxes unless the original uses separate text objects.
- Record `font_size_source: "measured"` and optional `box_px` / `glyph_height_px` on the spec element.
- Unicode symbols that still clip: widen the padded box, do not wrap a measured single-line label.

## 6b. Container → padding → children (design logic)

A slide is a **tree of containers**, not a flat list of free coordinates.

```
slide
 └─ frame / card
      ├─ header bar
      │    └─ title text   ← padded / centered inside the bar
      ├─ diagram box       ← inset from card edges
      │    ├─ nodes
      │    └─ labels       ← gap from the node they name (above/below/beside)
      └─ caption band      ← inset from card bottom; gap below diagram
```

Rules:

1. **Measure each parent against its neighbors** (card vs card, node vs node) as pixel boxes on the screenshot. Record `x,y,w,h` per element — **do not assume equal widths, heights, or gutters**. Example: bottom Sequential card is shorter; Parallel is narrower and sits under the Parallel top card, with a large gap after Sequential.
2. **Measure padding** = distance from parent edge to the first child ink / shape, and **gaps between siblings** (pill-to-pill, card-to-card).
3. **Place children relative to the parent**, never by absolute guess:
   - **Text vs shape (universal):** any text *inside* or *beside* a shape is measured against that shape before build. Inside → `measure_text_in_shape` + shape-native Edit Text + `pad_frac`. Beside → measured gap via `label_above` / `label_below` (or explicit box), aligned to the photo’s anchor. See [universal-measure-rule.md](universal-measure-rule.md).
   - Text *on* a filled shape (header title, “LLM” in a circle) → **shape-native text**: `set_shape_text` / `add_shape_with_text`. In PowerPoint this is select shape → **Edit Text**. Do **not** stack a separate text box on the shape — it won’t scale with the bar.
   - **Visual size rule:** measure the gap between text ink and the host fill on the screenshot (`measure_text_in_shape` → `pad_frac`, `glyph_pt`). Cap pt with `font_pt_fit_shape(..., pad_frac=…)`. Do not guess a large pt that fills the circle. Text must sit inside with the same breathing room as the photo. After a PowerPoint raster, confirm letters are not edge-to-edge.
   - Labels *near* a node (Input/Output beside a circle) → separate text box via `label_above` / `label_below` with **measured** `node_radius + gap` from the screenshot (not a default gap).
   - Caption under a diagram → **text placeholder** sized from measured gaps: distance from diagram (or shape) above → text ink, and from text ink → element/card below (`caption_band_box`). Set width so wrap matches the photo; `align` center or left as in the source. Do not let the box fill leftover empty space (that mis-wraps and floats the caption).
   - **Title placeholder above a rule:** measure pad from card top → title ink and from title ink → rule. Size/align the title band from those two distances.
   - **Rule / divider line:** if the photo shows the line touching the card’s left and right borders, draw it **full card width** (L/R contact). Do not inset with the content pad.
   - **Flowing diagram shapes** (fans, arrows, capsules, nodes): measure distance from the title/rule (or other upside shape) down to the first diagram ink, gaps between siblings, and pad to card edges. Place from those measurements — never “center in leftover” or stretch to fill the body.
   - **Flow-group measure:** when arrows + capsules (or similar) repeat as a unit, mentally (or actually) group them, take that group’s bbox, and record **pad L/R/T/B** against the parent card plus **internal** lengths (arrow shaft length, inter-row gap). Rebuild so the group insets and line lengths match — same length for every parallel arrow. **Apply to every sibling card**, not only the one the user pointed at.
4. **Sibling gutters** between cards in a row — measure each gap; they are often unequal when cards align under different parents.
5. **Aspect ratios** of pills/icons are properties of the shape, not of the card — do not stretch a pill to fill leftover height.
6. **Lines:** measure stroke weight (px → pt). If the photo has an arrowhead, use a connector with `end_arrow` / `begin_arrow` (PowerPoint Line → Arrow type). Do not draw `RIGHT_ARROW` shapes.

Helpers: `inset_box`, `center_in`, `text_in_box`, `caption_band_box`, `label_above` / `label_below`, `set_line_arrows`, `add_line` in `scripts/helpers.py`.

Ink-tight glyph boxes still drive **font size**. Container insets drive **where that text box sits**. Both are required.

## 7. Build order

1. Slide background
2. Frame / cards
3. Diagrams, icons
4. Text
5. Overlays (underlines, stickers)
6. `group_shapes(...)` per component

## 8. Grouping

Ungrouped slides fail the shape gate when `groups_required` is true (default).

Use `helpers.group_shapes`. Never append the group element into itself.

PowerPoint world coordinates are:

```
world = grp.off + (child.off − chOff) × (ext / chExt)
```

`group_shapes` must snapshot child EMUs, move the XML nodes, write **local** `a:off`, and set `chOff` to `(0, 0)` with `off` at the group's slide origin.

Do **not** assign `shape.left` / `shape.top` after the node is inside `p:grpSp`. python-pptx will rewrite `a:off` in the slide coordinate system. Combined with a non-zero `chOff`, PowerPoint double-subtracts and parks the group at the slide origin (last card stacked top-left). Inspecting `.left` still looks correct — that is not proof.

`pptx_inspect.py` computes child positions with the OOXML formula above. `coord_mode: DOUBLE_OFFSET_BUG` fails the shape gate.

## 9. Glyph-locked highlights

A colored bar behind part of a heading is locked to the **substring**, not to a second pixel blob from the screenshot.

Screenshot gold/yellow measurements pick up proofing squiggles and compression and come out too wide and shifted (covering adjacent characters). For CJK, advance = 1em = `size_pt / 72` inches. Center the full title on the slide, then:

```
left  = (slide_w − len(title)×em) / 2 + index(substring)×em
width = len(substring) × em
```

Use `helpers.cjk_centered_substring_box`. If the bar and the glyphs are independent measurements, they will drift.

## 10. Source-audit (spec vs original photo)

`verify_pptx.py` only diffs spec vs XML. A guessed spec will still pass. `scripts/source_audit.py` maps each spec text box back onto the screenshot and fails if:

- the box has no ink (`no_ink`, coverage < 4%)
- measured glyph height is off the declared pt (`glyph_height`, ratio outside 0.75–1.35)
- the box misses a `text_hints` line (`box_misses_line`, IoU < 0.15)

Warnings: `ungrounded_pt` when `font_size_source` is missing or `guessed`.

## 11. Delivery

Run `source_audit.py`, then `verify_pptx.py`, then `export_slide_png.py` + `compare_render.py`. Source, shape, font, color, **and** the PowerPoint raster must all pass. The user is not QC. Quick Look is not a valid render.
