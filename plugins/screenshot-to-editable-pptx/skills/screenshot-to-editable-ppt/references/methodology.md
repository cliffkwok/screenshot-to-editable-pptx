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

## 6. Text (glyph box + one box per line)

Do not guess pt. Do not size a box with `char_count × 0.6`.

```
latin_pt = glyph_h_px / img_h × slide_h_in × 72 / 0.72   # cap-height ≈ 0.72em
cjk_pt   = glyph_h_px / img_h × slide_h_in × 72 / 0.88
```

`scripts/text_hints.py` (Tesseract TSV → ink-refined box) writes `box_px`, `glyph_height_px`, `font_pt_if_latin` / `_cjk`, and a `size_group`. Same-level lines share the group's median pt. OCR strings can be dirty — Vision still owns the exact visible string; the hint owns the box and the pt.

Rules:

- One visual line = one PowerPoint text box. `add_line_text` / `add_text_from_hint` set `wrap=False`.
- Box = tight ink + pad (`pad_ink_box_px`, ~0.14w / 0.20h of glyph height).
- Centered titles still use `align="center"` inside that padded ink box — do not stretch the box to the full card unless the source does.
- Multi-line copy is stacked single-line boxes that share `size_group`. Do not put two visual lines in one wrapped frame.
- Record `font_size_source: "measured"` and optional `box_px` / `glyph_height_px` on the spec element.
- Unicode symbols that still clip: widen the padded box, do not wrap.

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
