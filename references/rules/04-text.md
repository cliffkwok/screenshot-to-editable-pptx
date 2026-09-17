# 04 — Text

**Category tag:** `text`  
**When to update:** mid-word wraps (`Coordinato/r`, `Agen/t`, `solutio/n`), wrong pt, edge-to-edge in-shape text, caption break mismatch, wrong host label, floating text not docked to neighbors.

## Law

> Every text element is a **text placeholder**.  
> 1. Measure the ink box (and photo wrap breaks).  
> 2. Measure distance to **neighbor shapes** (parent edges, sibling boxes, icons, **connector lines**).  
> 3. **Measure distance to every neighboring text run** (title→subtitle, label→body, sentence→link) — horizontal **and** vertical gaps in source px.  
> 4. Place / size the placeholder from those pads — never by leftover space.  
> Mid-word wraps in the screenshot are **defects** — rebuild as one line with width ≥ ink (+ pad).  
> **If you cannot measure a gap / color / size → stop and ask. Never guess.**

## Text-to-text gaps (mandatory)

Adjacent / stacked copy is **not** freehand. For every pair of distinct text runs that sit next to each other in the photo:

1. Measure **ink bbox A** and **ink bbox B** separately (PIL tight box).
2. Record `gap_px` = distance between facing edges (`B.left − A.right` or `B.top − A.bottom`).
3. Place so boxes **never cross** that gap. If PPT font is wider than ink, **widen the union** or use **one text frame with multiple runs** — do not add a second floating box that can overflow into the neighbor.
4. Inline link after a sentence (`… stay. Learn more`): prefer **one** placeholder; run 1 = sentence (+ trailing space), run 2 = link (`underline=True`). Union box = measured full-line ink.

Forbidden: guessing “Learn more” x; stacking two placeholders that share the same band; using title pt / box to infer subtitle gap.

## Text between shapes (corridor labels)

When a label sits **between** connectors / rules / container edges (“Tool usage” between dual arrows, “Cost” between vertical arrows):

1. Measure the **bounding edges** (arrow `y`/`x`, shape sides).
2. Measure the **ink box**.
3. Optically centered (equal side gaps) → `text_in_corridor(..., equal_gaps=True)`.
4. Asymmetric on purpose → record `gap_above` / `gap_below` / `gap_left` / `gap_right`.
5. Helper **raises** if the box would overlap a bound.
6. Forbidden: `mid_y = (a+b)/2` guesses, “put it near the arrows”, placeholder that crosses a line, unequal gaps when the photo is centered.

## Placeholder procedure (universal)

```
for each visible text run:
    ink_box  = PIL tight bbox of glyphs
    neighbors = parent shape, nearest sibling **shapes**, and nearest sibling **text runs**
    pads     = ink ↔ each neighbor edge (px)  # includes text↔text gaps
    wrap     = True iff photo shows 2+ lines in one band
    place with text_in_box / add_shape_with_text / caption_band_box(pads…)
    # adjacent inline runs → one frame + multiple runs when a shared baseline
```

| Photo situation | PPT |
|-----------------|-----|
| Label inside a box (Input / Output) | Shape-native Edit Text; margins from measured pads |
| Label near a host (Problem above node) | `label_above` / `label_below` with measured gap |
| Title / free label | `text_in_box(ink_box ± pad)` · `wrap=False` |
| Title above subtitle (stacked copy) | Measure **each** ink box + `gap_px` title→sub; left-align from photo |
| Caption that wraps in the photo | One placeholder · measure **line-1 ink width** · put the photo break in as `\n` (helpers split to paragraphs) · never rely on PPT auto-wrap alone |
| Soft-wrap lands on wrong word (`and` vs `not`) | Widen to line-1 width **and** explicit `\n` after the photo’s last word on line 1 |
| Mid-word break in source | Defect → widen + `wrap=False` |
| Photo shows **one** line but PPT wraps (Arial wider than UI font) | Keep `wrap=False`; widen box and/or allow slight right overflow — **never** `wrap=True` to “fit”. Wrapping invents a 2nd line and **destroys** measured title↔sub / sub↔card gaps |
| Label between dual arrows / rules | `text_in_corridor` from measured gaps (no overlap) |
| Sentence + inline link on one line | **One** text frame; two runs; measure union + inter-run gap |
| Value not readable from photo | **Ask** — never guess |

## Inside a filled shape (header, Agent, LLM circle, …)

1. Shape-native **Edit Text** (`set_shape_text` / `add_shape_with_text`).
2. Measure ink ↔ host on **all four sides** → `pad_frac` / margins / glyph pt.
3. Cap pt with `font_pt_fit_shape(..., pad_frac=…)`.
4. Default `wrap=False` for single-token / single-line labels.
5. If the photo shows one line but a narrow box caused `solutio\\nn`, **widen the shape** until one line fits; do not keep the broken wrap for “fidelity.”

## Near a shape (Problem / Solution / Workspace / title above card, …)

1. Correct **host** from the photo.
2. Measured gap; `label_above` / `label_below` / `label_centered_on_box` (no default gap).
3. **Titles above a container** must share the container’s **center x**  
   (`label_centered_on_box(outer, ink_w, ink_h, side="above", gap_px=…)`).  
   Forbidden: a wider guessed text box that only *looks* centered, or a left-biased x.
4. Align to host center or named segment.

## Font size

1. Measure **each** text element’s **cap-height** on the photo (capital letter / first-line caps — not full string bbox with descenders `q`/`g`).
2. Convert with `font_pt_from_glyph(cap_px, img_h, slide_h)` → `font_size_pt`.
3. `font_size_source: "measured"` on every text element in the spec.
4. Same visual level → same pt (title row, header row, caption row) — only after measuring siblings and confirming equal cap-height.
5. **Never** copy title pt onto an inner label, or guess pt because “it looked close.”

## Font weight (bold vs regular)

1. **Measure** stem thickness / compare to known bold neighbors — do not default `bold=True`.
2. UI chrome like “Back”, “Save & exit”, body copy is often **regular**; titles/CTAs may be bold — decide per run from the photo.
3. Wrong bold makes text look tighter (eats padding) and fails ORIGINAL|RENDER.

## Forbidden

| Anti-pattern | Do instead |
|--------------|------------|
| Keep `Agen/t` because the PNG has it | Widen + `wrap=False` |
| Guess pt to fill a circle | `measure_text_in_shape` + `pad_frac` |
| Reuse another element’s pt (title → agent header) | Measure that element’s own cap-height |
| Full-string ink height (includes descenders) as cap | Capital / cap-height only → `font_pt_from_glyph` |
| Default `bold=True` on labels / Back / chrome | Measure weight; regular unless photo is clearly bold |
| Stacked fake lines for a wrapped caption | One `wrap=True` placeholder |
| Default `gap=4` for labels | Measured gap to neighbors |
| Float text in leftover whitespace | Dock with measured pads to parent/siblings |
| Guess corridor label between arrows | `text_in_corridor` from measured gaps |
| Two placeholders for inline “sentence + link” that overlap | One frame, two runs; or boxes clamped to measured ink + gap |
| Guess title→subtitle / label→body gap | Measure both ink boxes → `gap_px`; place `B.top = A.bottom + gap` |
| `wrap=True` on a band that is one line in the photo | `wrap=False` + width slack — wrapping collapses vertical pads |
| Guess any value you did not measure | **Ask the user** — do not invent |

## Gate

`source_audit.py` (ink in box, glyph height) + `verify_pptx.py` → `gates.font`.
