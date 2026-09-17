## 2026-09-17 · text · measure bold vs regular; progress = track under fill

- **Deck:** Airbnb Add discounts  
- **Saw:** “Back” forced bold (photo is regular — looks tighter). Progress drawn as black chunks only; photo/teaching = **grey track at back + black fill on top** (overlapping layers). Title pt from full bbox (incl. descenders) overflowed and ate title↔sub gap.  
- **Rule:** (1) Measure font **weight** per run — no default bold. (2) Progress/scrubber = track (back) + fill (front). (3) `font_pt_from_glyph` from **cap-height**, not descender bbox. Checklist HARD items for text↔text + wrap remain.  
- **promoted:** yes → [04-text.md](04-text.md) + [05-lines-icons.md](05-lines-icons.md) + checklist

## 2026-09-17 · text · stacked gaps destroyed by wrap=True

- **Deck:** Airbnb Add discounts  
- **Saw:** User (again): title↔subtitle padding wrong. Photo = one-line subtitle + 13px gap + 23px to card. Build used `wrap=True` on ink-width box → Arial wrapped to 2 lines → optical gap collapsed.  
- **Rule:** Measure **all** stacked text gaps (`A.bottom→B.top`, `B.bottom→next`). Place `B.y = A.bottom + gap`. If photo is one line → **`wrap=False`** (widen / slight overflow OK). Never `wrap=True` to squeeze width — it invents lines and kills measured pads.  
- **promoted:** yes → [04-text.md](04-text.md)

## 2026-09-17 · text · always measure text↔text distance

- **Deck:** Airbnb Add discounts  
- **Saw:** “Learn more” floated at a guessed x → overlapped “Only one discount…”. Title→subtitle also needs its own measured gap (13px here), not a shared band guess.  
- **Rule:** For every neighboring text pair, measure **both** ink boxes + `gap_px` (H or V). Adjacent inline runs (sentence + link) → **one** text frame with multiple runs (or boxes that stop before the gap). Never guess a second placeholder’s origin.  
- **promoted:** yes → [04-text.md](04-text.md) + [01-measure.md](01-measure.md) + [universal-measure-rule.md](../universal-measure-rule.md)

## 2026-09-17 · delivery · no full-slide white backing shape

- **Saw:** User selected a full-slide white rectangle used as “background” — redundant on a white page and clutters the Selection Pane.  
- **Rule:** Solid page color → `set_background(slide, hex)` / `layout.background` only. Never add a full-slide same-as-bg rectangle. Color probe: `apply: "slide_background"`. Real panels (cards, hosts) that are *not* the page remain shapes.  
- **promoted:** yes → [02-color.md](02-color.md) + [layout-json.md](layout-json.md) + `build_pptx_from_layout.py` + `verify_pptx.py`

## 2026-09-17 · workflow · five universal enrichments (contact / png-fallback / layout build / OCR / job+repair)

- **Saw:** Peer skills (ningzimu / janechao / soulmujoco) add ops we lacked: contact sheets, PNG-visible+SVG-kept, layout JSON assemble, OCR strings, per-page jobs + local repair.  
- **Rule:** Adopt all five **around** measure gates — never replace measure with imagegen. Tools: `contact_sheet.py`, `build_pptx_from_layout.py`, `ocr_fill_text.py`, `init_job.py`; docs: `08-layers`, `09-job-workflow`, `layout-json`.  
- **promoted:** yes

## 2026-09-17 · layers · A/B/C split + vtracer for complex icons

- **Saw:** Public `slide-image-to-editable-pptx` uses visual/structure/text layers; our skill over-forced 3D icons into crude native shapes.  
- **Rule:** Classify A/B/C ([08-layers.md](08-layers.md)). A policy order: shape_group → `vectorize_region.py` (vtracer) → measured PNG picture. Never bake text into A; never full-slide paste. B/C still measured.  
- **promoted:** yes → [08-layers.md](08-layers.md) + scripts

## 2026-09-17 · layout · executive composition principles + layout/component mode

- **Saw:** User needs layout design principles (balance, hierarchy, focal point, unity, rhythm, whitespace, restrained variety) for page/section screenshots, without a separate skill.  
- **Rule:** Same skill, two modes. Infer layout vs component (override: `layout`/`component`/`全页`/`组件`). Layout → state takeaway + architecture brief, then measure under [07-layout.md](07-layout.md). Component → skip brief; measure nest/internals. Principles never invent pads the photo lacks.  
- **promoted:** yes → [07-layout.md](07-layout.md) + [universal-measure-rule.md](../universal-measure-rule.md) + SKILL + checklist

## 2026-09-17 · lines · hairline rules = PPT Line Weight (not filled rects)

- **Deck:** Airbnb Get Started  
- **Saw:** Step/footer dividers looked too heavy — built as 1px-tall filled rects (and sometimes doubled with Lines). Photo is a 1px hairline; PPT Weight menu match ≈ **¾ pt**.  
- **Rule:** Measure rule thickness → `stroke_px_to_pt` → snap to PPT Line Weight (¼/½/¾/1…). Use `add_line` only; never stack a filled rect + line for the same rule.  
- **promoted:** yes → [05-lines-icons.md](05-lines-icons.md)

## 2026-09-17 · measure · every element vs neighbors (procedure — any screenshot)

- **Context:** AI System doc icon (circle + dashed lines) exposed the failure mode; the fix is **not** those numbers.  
- **Saw:** Nest pads fixed, but badge↔content still wrong because build used guessed body-height fractions. Same class of bug will hit any deck if we only hardcode one nest.  
- **Rule (universal procedure):** On **every** new screenshot: (1) detect elements on *this* photo; (2) measure each neighbor gap; (3) measure internal stacks (badge→line0, …); (4) place only from those measurements; (5) **never copy** pads/`line_y_fracs`/badge sizes from a previous work folder. Promote process → `universal-measure-rule.md` + helpers `measure_dashed_lines_under` / `lines_under_anchor`.  
- **promoted:** yes → [universal-measure-rule.md](../universal-measure-rule.md) + [01-measure.md](01-measure.md) + `helpers.measure_dashed_lines_under`

## 2026-09-17 · measure · nested host L/R from vertical dashed walls

- **Deck:** AI System (Task / Eval Data / Grader)  
- **Saw:** Host L/R taken from the **top horizontal dashed span** → rounded corners clip that span inward → reported `pad_L/R ≈ 1–2px` while the eye sees ~18–19px inset. User: “three boxes have space with the bigger box.” Real walls are at x≈16 / x≈267 (vertical dashed columns).  
- **Rule:** Measure host **top/bottom** from horizontal dashed envelopes; measure host **L/R** from **vertical dashed** columns *outside* the body cluster (`_dashed_v_edge`). Never use top-row min/max x alone on rounded dashed hosts. Badges that sit fully inside the body use `badge_inside_body_top` + measured `badge_pad_T` — do not assume edge-dock.  
- **promoted:** yes → [01-measure.md](01-measure.md) + `scripts/measure_nested_pack.py`

## 2026-09-17 · text · title centered on host box

- **Deck:** AI System  
- **Saw:** “AI System” used guessed box `(512,18,180,22)` → text not on outer center; photo ink is `(587,11,105,23)` with `cx == outer_cx`.  
- **Rule:** Labels above a container use measured ink w/h + `label_centered_on_box` (or equivalent): `x = parent_cx − ink_w/2`, `y = parent_top − gap − ink_h`. Never a wider placeholder that drifts off-center.  
- **promoted:** yes → [04-text.md](04-text.md) + `helpers.label_centered_on_box`

## 2026-09-17 · color · eyedropper only (no guess / no AA)

- **Deck:** AI System  
- **Saw:** Wrong Agent/Eval colors; user Colors panel showed `#B45654` while nearby AA read `#C76665`. Agent “fill” sample hit text halo (`#ADA2A0`) instead of true fill `#5D3736`. Stroke often un-probed so gate passed.  
- **Rule:** Use `scripts/eyedropper.py` (1×1 pixel) or the user’s Colors panel Hex. Fill ≠ stroke ≠ ink; probe **both** fill and stroke. Panel hex wins. Never average / guess / sample fringe.  
- **promoted:** yes → [02-color.md](02-color.md) + `scripts/eyedropper.py`

## 2026-09-17 · lines+text · tip touches box + equal corridor gaps

- **Deck:** AI System  
- **Saw:** (1) Dual arrows stopped short of Eval (~10–15px air gap). (2) “Cost” had unequal left/right gaps between vertical lines. (3) Nest labels stretched into `pad_B` → flush bottom / empty top.  
- **Rule:** Arrow endpoints = `point_on_edge` on the target stroke (`t` from photo); verify tip touches after export. Corridor labels that should look centered use `text_in_corridor(..., equal_gaps=True)`. Nest labels = ink-sized box + measured `label_gap` — never `h = pad_B`.  
- **promoted:** yes → [05-lines-icons.md](05-lines-icons.md) + [04-text.md](04-text.md) + `text_in_corridor(equal_gaps=…)`

## 2026-09-17 · process · never guess — measure or ask

- **Deck:** AI System  
- **Saw:** Guessed Eval stroke (`#A4A778` vs measured `#B5BB7D`); guessed “Tool usage” / “Cost” into arrow corridors → text overlapped lines; guessed nest pads. Each guess cost a full rebuild + user correction.  
- **Rule:** If a fill/stroke/ink, pad, gap, pt, or corridor position is not measured from the photo → **stop and ask**. Do not invent hex, midpoints, or “near the arrows.” Asking once is cheaper than a wrong PPTX.  
- **promoted:** yes → [04-text.md](04-text.md) + [01-measure.md](01-measure.md) + cursor rule

## 2026-09-17 · text · corridor labels between connectors

- **Deck:** AI System  
- **Saw:** “usage” bisected by bottom arrow; “Cost” not in the measured gap between vertical arrows. Placement used `EVAL+8` / `outer+20` guesses.  
- **Rule:** Labels between shapes/lines use measured ink + `gap_above/below/left/right` via `text_in_corridor` (hard no-overlap).  
- **promoted:** yes → [04-text.md](04-text.md) + `helpers.text_in_corridor`

## 2026-09-17 · measure · nested host pads + sibling hgap (not guessed padding)

- **Deck:** AI System (Task / Eval Data / Grader packs)  
- **Saw:** Dashed host + 3 doc icons placed by eyeballed padding → wrong gaps, host too tight/loose, labels drifted. Fan-out dashes polluted host bbox.  
- **Rule:** For every nested pack: (1) measure **child bodies** first (vertical stroke runs); (2) measure **host** from top dashed envelope + bottom span *below labels* (labels stay inside host); (3) record `pad_L/T/R/B`, uniform `body_w/h`, `hgap`; (4) place with `nested_row_from_pads` — `body[i]=(host.x+pad_L+i*(body_w+hgap), host.y+pad_T, body_w, body_h)`; (5) badge via `badge_on_body_top`; (6) `assert_children_inside`. Never invent padding. Tool: `scripts/measure_nested_pack.py`.  
- **promoted:** yes → [01-measure.md](01-measure.md) + `helpers.pads_in_parent` / `nested_row_from_pads` / `badge_on_body_top`

## 2026-09-17 · color · measure every role (fill ≠ stroke ≠ ink)


- **Deck:** AI Evals  
- **Saw (repeated):** (1) Step-3 disc used bright-blue **stroke** as solid **fill** — photo is navy fill `#27384C` + blue ring `#4791D8`. (2) Claim ✓/✕ painted **white**; photo ink is near-**black**. (3) Badge/rect colors guessed.  
- **Rule:** For every shape measure **fill**, **stroke**, and **glyph ink** separately (circle fill at `r_frac<0.5`). Never assume white/black marks. Guessed hex = fail.  
- **promoted:** yes → [02-color.md](02-color.md)

## 2026-09-17 · measure · badge dock on host edge

- **Deck:** AI Evals step-2  
- **Saw:** White “2” circle and green RAG rect are **two shapes**; badge center sits on rect **top** edge (`cy ≈ top`), measured inset from right.  
- **Rule:** Overlay badges = separate shape; measure `badge_cy - host_top` and `host_right - badge_cx` (or left); place from those distances — not eyeball.  
- **promoted:** yes → [01-measure.md](01-measure.md)

## 2026-09-17 · lines · Line arrow + curve are properties


- **Deck:** AI Evals  
- **Saw:** Judge→claims built as diagonal+horizontal straight segments (sharp elbows, no tips). Photo is a **rounded bracket fan** with open arrowheads on each claim.  
- **Rule:** Connectors are PPT **Line** shapes; set `kind` (straight/elbow/curve) and `end_arrow`/`begin_arrow` as line properties. Use `fan_out_lines` for 1→N. Never fake bends with two straights or Arrow AutoShapes.  
- **promoted:** yes → [05-lines-icons.md](05-lines-icons.md) + `helpers.add_line(kind=…)` + `helpers.fan_out_lines`

## 2026-09-17 · text · each label’s own cap-height → pt


- **Deck:** Sequential agent  
- **Saw:** Title “Sequential agent” at 49pt and agent-header same string at 20pt — both oversized vs photo (cap 31px→39.7pt, 12px→15.4pt). Spec claimed `font_size_source: measured` but pts were guessed / reused.  
- **Rule:** Measure **every** text element’s **cap-height** (capital, not full-string with descenders) → `font_pt_from_glyph`. Never copy title pt to inner labels. Already required by measure law; made explicit in 04-text.  
- **promoted:** yes → [01-measure.md](01-measure.md) + [04-text.md](04-text.md)

## 2026-09-17 · text · soft-wrap needs real paragraphs

- **Deck:** Sequential agent  
- **Saw:** Photo caption breaks after **not**; render broke after **and** (or mangled) because `add_text` put the whole string (incl. `\n`) in one run — PPT ignores `\n` in a run.  
- **Rule:** Split `text` on `\n` into separate paragraphs; size the placeholder to **line-1 ink width**; never rely on PPT auto-wrap alone for photo soft-wraps.  
- **promoted:** yes → [04-text.md](04-text.md) + `helpers.add_text`

## 2026-09-17 · export · capture PPT window id not desktop

- **Saw:** Full-display `screencapture` grabbed Cursor chrome; caption compare looked empty / MAE spiked.  
- **Rule:** Export via slideshow window (`screencapture -l <CGWindow id>`); reject dark/non-slide grabs.  
- **promoted:** yes → `scripts/export_slide_png.py`

## 2026-09-17 · delivery · always show original vs output

- **Saw:** User asked that every result include original + output comparison while the skill is being hardened.  
- **Rule:** After each rebuild, export + `compare_render`, then **show** `compare_side_by_side.png` (and keep `original.png` / `render.png`) — never pptx-only.  
- **promoted:** yes → [06-delivery.md](06-delivery.md) + Cursor rule standing order

## 2026-09-17 · shape · ask round vs sharp per rectangle

- **Deck:** Sequential agent  
- **Saw:** Defaulted Input/Output/subs to rounded; photo corners are **sharp** (stroke meets at corner). Only the large agent frame is slightly round (~3px).  
- **Rule:** For every rectangle ask sharp/slight/round via `classify_rect_corner` → `RECTANGLE` or `ROUNDED_RECTANGLE`+`rad`. Never default the whole slide to rounded.  
- **promoted:** yes → [03-shape.md](03-shape.md) + `helpers.classify_rect_corner`

## 2026-09-17 · text · placeholder + neighbor pads

- **Deck:** Sequential agent  
- **Saw:** Labels floated / caption wrap wrong when boxes were placed first and text filled leftover.  
- **Rule:** Every text run = **placeholder**: measure ink + wrap, then dock with measured gaps to parent/sibling shapes (`text_in_box` / `add_shape_with_text` / `caption_band_box`).  
- **promoted:** yes → [04-text.md](04-text.md)

# Learnings log

Append-only. Each entry: date · category · one-line rule · optional deck.

When a line is promoted into `01`–`06`, mark `promoted: yes`.

---

## 2026-09-17 · lines · stacked crosshair marker detector

- **Deck:** Claude Cowork intermediate  
- **Saw:** Selected marker looked like one blue pin; photo is **grey H track + grey V stem + blue circle** stacked. Stem was wrongly painted accent blue.  
- **Rule:** Always decompose; run `detect_stacked_marker.py`; build with `add_crosshair_marker` (stem color = track grey). Encode in [05-lines-icons.md](05-lines-icons.md).  
- **promoted:** yes → `scripts/detect_stacked_marker.py` + `helpers.add_crosshair_marker`

## 2026-09-17 · color · panel hex beats PIL AA

- **Deck:** Claude Cowork intermediate  
- **Saw:** INTERMEDIATE looked washed (`#385A97` / `#698EC4` from PIL) vs macOS Colors panel **`#3C5599`** (R60 G85 B153).  
- **Rule:** When a Color Picker / RGB Sliders crop is provided, that hex is authoritative. Probe with `"source": "panel"`; verify checks PPTX only (skips screenshot AA re-sample).  
- **promoted:** yes → [02-color.md](02-color.md) + `verify_pptx` panel source

## 2026-09-17 · color+lines+shape · ink hex + stroke px + shadow panel

- **Deck:** Claude Cowork intermediate  
- **Saw:** INTERMEDIATE text too light (`#688EC8` vs core `#385A97`); track Pt guessed not measured; selected marker was one oval+line not a group; icon shadow not matching panel (Transparency 18% / Size 101% / Blur 11 pt / Angle 90° / Distance 4 pt).  
- **Rule:** Sample **darkest-quartile core ink** for text hex. Convert stroke **px → pt** with `stroke_px_to_pt`. Composite controls = grouped shapes (stem + thumb). Shadows use **all** panel fields via `add_shadow(blur_pt=, dist_pt=, transparency_pct=, size_pct=, dir_angle=)`.  
- **promoted:** yes → helpers `add_shadow` (+ `size_pct`→sx/sy) + [02-color.md](02-color.md) + [03-shape.md](03-shape.md) + [05-lines-icons.md](05-lines-icons.md)

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
