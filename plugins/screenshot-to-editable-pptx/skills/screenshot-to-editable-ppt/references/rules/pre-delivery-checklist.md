# Pre-delivery checklist (before any user-facing output)

**Hard gate.** Do **not** open the `.pptx`, paste a path, or say “done” until every category below is checked **and** the three automated gates pass.

Categories live in [rules/](rules/README.md). New corrections → [rules/LEARNINGS.md](rules/LEARNINGS.md) → promote into the matching file.

---

## A. By category (manual / agent self-check)

### Measure — [01-measure.md](rules/01-measure.md)
- [ ] Each card/parent measured independently (no assumed equal gutters)
- [ ] **Nest:** `python3 scripts/nest_detect.py --image … --self-test` PASS; diagram inset pads used
- [ ] **Nested children:** `assert_children_inside(parent, …)` PASS before `group_shapes` (no child taller/wider than nest)
- [ ] Flow-group `pad_L/R`, `pad_from_rule` / `pad_T`, `pad_B` (not leftover center)
- [ ] Fans not glued to divider unless photo shows join
- [ ] Captions via `caption_band_box` (pad to neighbors)
- [ ] Dividers full parent width when photo shows L/R contact
- [ ] Same pattern applied to **all** siblings

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
- [ ] Wrap from photo; **mid-word wraps treated as defects** (widen + one line)
- [ ] Captions: wrap only if photo wraps; width matches break points

### Lines / icons — [05-lines-icons.md](rules/05-lines-icons.md)
- [ ] Stroke weight per role
- [ ] Straight / elbow / curve from photo; Line arrows (not AutoShapes)
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
3. That the category checklist was completed

If anything in A or B fails → **stop**. No “almost done” delivery.
