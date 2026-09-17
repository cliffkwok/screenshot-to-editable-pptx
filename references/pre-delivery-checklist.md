# Pre-delivery checklist (before any user-facing output)

**Hard gate.** Do **not** open the `.pptx`, paste a path, or say “done” until every category below is checked **and** the three automated gates pass.

Categories live in [rules/](rules/README.md). New corrections → [rules/LEARNINGS.md](rules/LEARNINGS.md) → promote into the matching file.

---

## A. By category (manual / agent self-check)

### Mode
- [ ] **layout** vs **component** inferred (or user override) — [07-layout.md](rules/07-layout.md) / [universal-measure-rule.md](universal-measure-rule.md)

### Layout — [07-layout.md](rules/07-layout.md) *(layout mode only)*
- [ ] Core takeaway + layout architecture named before build
- [ ] Focal point / hierarchy / whitespace match the photo (not invented)
- [ ] Repeated cards share measured gutters; icon style unified as in photo

### Layers — [08-layers.md](rules/08-layers.md)
- [ ] Every element tagged A / B / C (`_layers.json` / `layer_inventory.py --check`)
- [ ] Layer A: shape_group **or** vectorize **or** measured PNG — no text in assets
- [ ] **Contact sheet** reviewed (`assets/_contact_sheet.png`)
- [ ] **png-fallback**: visible PPT image is PNG when SVG also exists
- [ ] Layer C text never baked into pictures; no full-slide screenshot paste

### Job — [09-job-workflow.md](rules/09-job-workflow.md)
- [ ] Job dir / per-page folders when multi-page (`init_job.py`)
- [ ] Assemble via `layout.json` + `build_pptx_from_layout.py` when using universal path
- [ ] Failures fixed with **local repair** (not full-page rebuild)

### Measure — [01-measure.md](rules/01-measure.md)
- [ ] **This screenshot only:** pads/gaps re-measured on *this* photo (no numbers copied from another work folder) — [universal-measure-rule.md](universal-measure-rule.md)
- [ ] Each card/parent measured independently (no assumed equal gutters)
- [ ] **Nest:** `python3 scripts/nest_detect.py --image … --self-test` PASS; diagram inset pads used
- [ ] **Nested pack:** host L/R from vertical dashed walls; `measure_nested_pack.py` / `nested_row_from_pads`
- [ ] **Nested children:** `assert_children_inside(parent, …)` PASS before `group_shapes` (no child taller/wider than nest)
- [ ] **Internal stacks** (badge→lines, icon→caption, …): measured gap + counted children — not guessed parent-height fractions (`measure_dashed_lines_under`)
- [ ] **Sibling gaps:** measured `h` + uniform `vgap`/`hgap`; widen stops before next sibling (`assert_min_gap`)
- [ ] Flow-group `pad_L/R`, `pad_from_rule` / `pad_T`, `pad_B` (not leftover center)
- [ ] Fans not glued to divider unless photo shows join
- [ ] Captions via `caption_band_box` (pad to neighbors)
- [ ] Dividers full parent width when photo shows L/R contact
- [ ] Same **procedure** applied to **all** siblings (re-measure each; do not clone one card’s coords blindly)

### Color — [02-color.md](rules/02-color.md)
- [ ] Hex PIL-sampled (not guessed)
- [ ] Font probes on darkest ink; bg on true page corner
- [ ] `color_probes` present; fill/font match photo + PPTX

### Shape — [03-shape.md](rules/03-shape.md)
- [ ] Correct primitive (ellipse→`OVAL`, not octagon)
- [ ] 3D blocks = back+front; dog-ears / wedges measured
- [ ] No accidental overlaps; radius matches photo

### Text — [04-text.md](rules/04-text.md)
- [ ] In-shape: ink↔host T/B/L/R; shape-native Edit Text; `pad_frac`
- [ ] Near-shape: correct host + measured gap
- [ ] **Text↔text (HARD):** for every neighboring text pair, record ink boxes + `gap_px` in the build/spec; place `B` as `A.bottom/right + gap` — never freehand y/x
- [ ] **Stacked title/sub (HARD):** crop ORIGINAL|RENDER of that band. Photo line-count must match render. If photo is 1 line → build must use `wrap=False`. **FAIL** if render wraps and collapses the gap
- [ ] **Font weight:** each run bold/regular matches photo (do not default bold on Back/chrome)
- [ ] Inline sentence+link = one frame / two runs (no overlay from dual placeholders)
- [ ] Photo one-line bands use `wrap=False` (do not wrap to “fit” — that kills vertical pads)
- [ ] Wrap from photo; **mid-word wraps treated as defects** (widen + one line)
- [ ] Captions: wrap only if photo wraps; width matches break points

### Lines / icons — [05-lines-icons.md](rules/05-lines-icons.md)
- [ ] Stroke weight per role
- [ ] Straight / elbow / curve from photo; Line arrows (not AutoShapes)
- [ ] **Progress/scrubber:** grey **track** (back) + fill (front) — two overlapping layers, not fill-only chunks
- [ ] **Docking:** endpoints on edges (`point_on_edge`); fan-in staggered (`edge_attach_ts`) — no N→one mid pile-up
- [ ] Composite icons = top-level groups; connectors outside

If any box fails → fix, rebuild, re-check. Do not deliver a partial.

---

## B. Automated gates (must all exit 0)

```bash
python3 scripts/source_audit.py --spec work/.../spec.json --original work/.../original.png \
  --hints work/.../text_hints.json --out work/.../source_audit.json

python3 scripts/verify_pptx.py --pptx <out.pptx> --spec work/.../spec.json \
  --original work/.../original.png --out work/.../verify_report.json

python3 scripts/export_slide_png.py --pptx <out.pptx> --out work/.../render.png

python3 scripts/compare_render.py --original work/.../original.png \
  --render work/.../render.png --out work/.../compare
```

- [ ] `source_audit` PASSED  
- [ ] `verify_pptx` PASSED (shape / font / color)  
- [ ] `compare_render` PASSED  

---

## C. Delivery statement (required)

Only after A + B, tell the user:

1. Path to the `.pptx`
2. That all three gates passed
3. That the category checklist was completed — **including Text HARD items** (text↔text `gap_px` recorded; stacked bands ORIGINAL|RENDER line-count match; no `wrap=True` on photo one-liners)

If anything in A or B fails → **stop**. No “almost done” delivery.
