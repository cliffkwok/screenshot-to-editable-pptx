# Learnings log

Append-only. Each entry: date · category · one-line rule · optional deck.

When a line is promoted into `01`–`06`, mark `promoted: yes`.

---

## 2026-09-17 · delivery · centered composition compare

- **Deck:** Claude Cowork intermediate  
- **Saw:** nest_detect SKIP (no header/stroke cards); compare_render used to fail with “no cream cards.”  
- **Rule:** When both original and render have 0 cards, gate on pixel MAE (≤55) instead of card IoU. Spec `layout_model: centered_composition`.  
- **promoted:** yes → [06-delivery.md](06-delivery.md) + `compare_render.py`

## 2026-09-17 · measure · Eagle Master Layout nest batch

- **Source:** Eagle `Master Layout.library` (15 screenshots) via `scripts/eagle_batch_selftest.py`  
- **Saw:** 0/15 pass — detector only knew solid colored headers; diagram frames are often tan/gray; Pros/Cons are stroke cards; sparse diagram ink was merging into headers.  
- **Rule:** `is_frame_stroke` + `diagram_score`; `stroke_card` fallback; header merge fill filter; SKIP non-nestable layouts. Run Eagle batch after nest_detect changes.  
- **promoted:** yes → [01-measure.md](01-measure.md) + `eagle_batch_selftest.py`

## 2026-09-17 · measure+lines · sibling gaps + docked fan-in

- **Deck:** AI agent design patterns (Competitive)  
- **Saw:** Agent/solution gaps wrong; solution→Evaluator lines all met at one mid-point → overlapping bundle; Problem hub not at measured left mid.  
- **Rule:** Measure `h`+`vgap`/`hgap` (`uniform_stack`/`assert_min_gap`); connectors use `point_on_edge`; fan-in uses `edge_attach_ts` — never N lines to one center. Auto compare→learn after every rebuild.  
- **promoted:** yes → [01-measure.md](01-measure.md) + [05-lines-icons.md](05-lines-icons.md) + [06-delivery.md](06-delivery.md)

## 2026-09-17 · measure · nested children must fit parent before group

- **Deck:** AI agent design patterns (Cooperative group)  
- **Saw:** Selecting the Cooperative group showed piled Agents / Synthesizer / fan — workspace was 155px tall inside a 143px diagram nest.  
- **Rule:** Parent-local layout + `assert_children_inside` before `group_shapes`. Never size a child larger than the nest box. Clamp label widen to parent.  
- **promoted:** yes → [01-measure.md](01-measure.md) + `abs_in_parent` / `assert_children_inside`

## 2026-09-17 · measure · box-inside-box nest detector

- **Deck:** AI agent design patterns (+ Eagle Master Layout batch)  
- **Saw:** Card contains header + inset diagram frame + caption; rebuilds ignored inset pads  
- **Rule:** Detect nest with `scripts/nest_detect.py`; place from `pads_in_parent`. Diagram must span most of card width (reject widget false-positives). Pale gold frames need loose stroke preds.  
- **promoted:** yes → [01-measure.md](01-measure.md) + `scripts/nest_detect.py`

## 2026-09-16 · text · mid-word wraps are defects

- **Deck:** AI agent design patterns  
- **Saw:** `Coordinato/r`, `Agen/t`, `solutio/n` in source PNG  
- **Rule:** Do not preserve mid-word wraps for fidelity. `wrap=False`, widen host until one line fits (+ measured pad).  
- **promoted:** yes → [04-text.md](04-text.md)

## 2026-09-16 · shape · ellipse ≠ octagon

- **Deck:** AI agent design patterns  
- **Saw:** Workspace rendered as octagon; photo is smooth ellipse  
- **Rule:** Photo ellipse/circle → `OVAL` only. Never polygon-approximate.  
- **promoted:** yes → [03-shape.md](03-shape.md)

## 2026-09-16 · shape · 3D agents need back+front

- **Deck:** AI agent design patterns  
- **Saw:** Flat blurry rects vs isometric agent blocks  
- **Rule:** 3D block = offset back plate + front face (optionally grouped).  
- **promoted:** yes → [03-shape.md](03-shape.md)

## 2026-09-16 · measure · header+diagram share outline

- **Deck:** AI agent design patterns  
- **Saw:** Tall colored header flush with card; diagram frame continues same hue  
- **Rule:** Measure header solid band and diagram body separately; don’t let body content that shares the header hue inflate `HDR_H`.  
- **promoted:** yes → [01-measure.md](01-measure.md) / [03-shape.md](03-shape.md)

## 2026-09-16 · delivery · compare cards = colored headers, not cream-only

- **Deck:** AI agent design patterns  
- **Saw:** `compare_render` found orig cards via red/yellow headers but 0 render cards when flood-fill merged header+frame into a tall blob  
- **Rule:** Detect cards with **row-band** header density (not flood-fill). Cream is fallback. Same-hue diagram borders must not swallow the header bar.  
- **promoted:** yes → [06-delivery.md](06-delivery.md) + `scripts/compare_render.py`

## 2026-09-16 · color · probe ink not AA fringe

- **Deck:** AI agent design patterns  
- **Saw:** Title probe `#4F4F4F` (fringe) vs PPT `#1A1A1A`  
- **Rule:** Sample darkest glyph pixel for font probes; page corner for bg — not frame chrome.  
- **promoted:** yes → [02-color.md](02-color.md)

## 2026-09-16 · delivery · checklist before any user-facing output

- **Rule:** Pre-delivery checklist (all categories) + three gates before path/“done”.  
- **promoted:** yes → [06-delivery.md](06-delivery.md)
