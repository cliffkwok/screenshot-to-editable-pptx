# Universal measure rule (index)

**Mandatory on every screenshot → editable PPT rebuild.**

This is a **procedure for any new screenshot**, not a one-shot fix for one deck.
Never reuse pads, gaps, `line_y_fracs`, badge sizes, or host boxes from a previous
build — **re-measure on the photo in front of you**.

Rules are split by category so corrections stay small and reusable:

→ **[rules/README.md](rules/README.md)** — category index  
→ **[rules/LEARNINGS.md](rules/LEARNINGS.md)** — append-only log (you teach → we promote)

| Tag | File |
|-----|------|
| `measure` | [rules/01-measure.md](rules/01-measure.md) |
| `color` | [rules/02-color.md](rules/02-color.md) |
| `shape` | [rules/03-shape.md](rules/03-shape.md) |
| `text` | [rules/04-text.md](rules/04-text.md) |
| `lines` | [rules/05-lines-icons.md](rules/05-lines-icons.md) |
| `delivery` | [rules/06-delivery.md](rules/06-delivery.md) |
| `layout` | [rules/07-layout.md](rules/07-layout.md) |
| `layers` | [rules/08-layers.md](rules/08-layers.md) |
| `job` | [rules/09-job-workflow.md](rules/09-job-workflow.md) |

## Universal pipeline (any screenshot)

```text
init_job (optional multi-page)
  → mode (layout|component)
  → layers A/B/C inventory
  → Layer A crops (+ vtracer SVG if available) → contact_sheet
  → measure B/C → layout.json
  → optional ocr_fill_text (strings only)
  → build_pptx_from_layout
  → gates + ORIGINAL|RENDER
  → local repair if needed
```

## Mode: layout vs component

Pick a mode **before** measuring (user may override with `layout` / `component` / `全页` / `组件`):

| Signal | Mode |
|--------|------|
| Full page/section, header/footer, multi-column, several regions | **layout** → apply [07-layout.md](rules/07-layout.md) brief, then measure |
| Tight crop: one widget, nest pack, icon, badge cluster | **component** → skip layout brief; measure internals |

Ambiguous → ask once, or default to **layout** if the frame has clear page chrome.

## Core law (all categories)

> **Measure every element against its neighbors** (up / down / left / right).  
> Position = f(those distances).  
> **Nothing** is placed by leftover space, eyeballing, or “center in the remaining box.”  
> **Inside a shape counts too** — badge→content lines, icon→caption, title→rule are
> each their own measured gap. Guessed fractions of parent `h`/`w` are forbidden.  
> **Text↔text counts too** — title→subtitle, label→body, sentence→link: measure each
> run’s ink box and the gap between them. Never guess an inline link’s x.  
> **No guessing:** if a pad / color / gap / pt cannot be read → **ask**, do not invent.

When the user corrects one card or label: **apply the same rule to every similar
element on this screenshot**, append [rules/LEARNINGS.md](rules/LEARNINGS.md),
promote into the matching category file — so the **next** screenshot inherits the
rule, not the numbers.

## Per-screenshot procedure (any deck)

Run this loop on **every** new image. Do not skip because a prior deck “looked similar.”

1. **Detect** each box / badge / line / label independently on *this* photo.
2. **Neighbor gaps** — for every parent→child and sibling pair, record
   `pad_L/T/R/B` or `gap` in source px (`pads_in_parent`, corridor helpers).
3. **Nested host** (dashed/stroked pack): top/bottom from horizontal envelopes;
   **L/R from vertical walls** (rounded corners clip the top span — do not trust
   top-row min/max x alone). Tool: `scripts/measure_nested_pack.py`.
4. **Internal stacks** (circle + dashed lines, etc.): measure
   `anchor_bottom → first child`, count children from the photo, measure inter-gaps.
   Place with measured ys / `line_y_fracs` — never `(0.38, 0.52, …)` guesses.
   Helper: `measure_dashed_lines_under` / nest script `measure_inner_lines`.
5. **Badges:** two shapes. Edge-docked → `badge_on_body_top`; fully inside →
   `badge_inside_body_top` + measured `badge_pad_T`. Decide from **this** photo.
6. **Place** only from those measurements; `assert_children_inside` where nested.
7. **Gates** + ORIGINAL|RENDER. If the eye sees a gap the numbers miss → re-measure,
   do not “nudge.”

**Hard fail:** copying `pad_L=18`, `badge_d=23`, or `line_y_fracs=[…]` from another
work folder into a new screenshot.

## Pre-build (quick)

See [pre-delivery-checklist.md](pre-delivery-checklist.md) — organized by the same categories.

## Helpers

`caption_band_box`, `inset_box`, `measure_text_in_shape`, `font_pt_fit_shape`,
`pads_in_parent`, `nested_row_from_pads`, `badge_on_body_top`, `badge_inside_body_top`,
`measure_dashed_lines_under`, `lines_under_anchor`,
`label_above` / `label_below` / `label_centered_on_box`,
`text_in_corridor`, `point_on_edge`,
`add_line` + `set_line_arrows`, `stroke_px_to_pt`,
`add_shadow(blur_pt=, dist_pt=, transparency_pct=, size_pct=, dir_angle=)`,
`add_pill_icon`, `group_shapes` — `scripts/helpers.py`.

Nested pack detector: `scripts/measure_nested_pack.py`.
