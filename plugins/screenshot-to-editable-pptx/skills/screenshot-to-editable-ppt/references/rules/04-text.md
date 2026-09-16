# 04 — Text

**Category tag:** `text`  
**When to update:** mid-word wraps (`Coordinato/r`, `Agen/t`, `solutio/n`), wrong pt, edge-to-edge in-shape text, caption break mismatch, wrong host label.

## Law

> Wrap **from the photo**, not from a guessed box width.  
> Mid-word wraps in the screenshot are **defects** — rebuild as one line with width ≥ ink (+ pad).

## Inside a filled shape (header, Agent, LLM circle, …)

1. Shape-native **Edit Text** (`set_shape_text` / `add_shape_with_text`).
2. Measure ink ↔ host on **all four sides** → `pad_frac` / margins / glyph pt.
3. Cap pt with `font_pt_fit_shape(..., pad_frac=…)`.
4. Default `wrap=False` for single-token / single-line labels.
5. If the photo shows one line but a narrow box caused `solutio\\nn`, **widen the shape** until one line fits; do not keep the broken wrap for “fidelity.”

## Near a shape (Problem / Solution / Workspace, …)

1. Correct **host** from the photo.
2. Measured gap; `label_above` / `label_below` (no default gap).
3. Align to host center or named segment.

## Placeholders (titles / captions)

| Photo | PPT |
|-------|-----|
| One visual line | `wrap=False`, width ≥ ink |
| Two+ lines in one band | `wrap=True`, one placeholder; width so breaks match photo |
| Mid-word break in source | Treat as defect → single line |

Helper: `caption_band_box` for pad-to-neighbors under a diagram.

## Font size

1. From glyph height on the photo (`text_hints.py` / measured ink).
2. `font_size_source: "measured"` on every text element in the spec.
3. Same visual level → same pt (title row, header row, caption row).

## Forbidden

| Anti-pattern | Do instead |
|--------------|------------|
| Keep `Agen/t` because the PNG has it | Widen + `wrap=False` |
| Guess pt to fill a circle | `measure_text_in_shape` + `pad_frac` |
| Stacked fake lines for a wrapped caption | One `wrap=True` placeholder |
| Default `gap=4` for labels | Measured gap |

## Gate

`source_audit.py` (ink in box, glyph height) + `verify_pptx.py` → `gates.font`.
