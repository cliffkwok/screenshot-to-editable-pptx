# 06 — Delivery

**Category tag:** `delivery`  
**When to update:** new gate, new checklist item, “don’t send until…”, compare detector improvements.

## Law

> Do **not** give the user a `.pptx` path, open the file, or say “done” until checklist **A** and gates **B** all pass. Statement **C** is required on delivery.

## Show original + output every time (skill-building phase)

Until the skill is stable, **every** user-facing result must include a visual comparison — no pptx-only replies:

1. Export → `compare_render.py`
2. Open / attach `compare/compare_side_by_side.png` (ORIGINAL | POWERPOINT RENDER)
3. Also keep `original.png` + `render.png` available
4. In the chat: one-line gate status (audit / verify / MAE) **plus** the side-by-side

Do not say “looks better” without showing both sides.

## A. Category checklist (before gates)

Run through every category — tick in [../pre-delivery-checklist.md](../pre-delivery-checklist.md):

- [ ] **Measure** — pads / flow-group / no leftover placement / siblings
- [ ] **Color** — sampled hex + probes
- [ ] **Shape** — correct primitives, no bad overlaps
- [ ] **Text** — wrap-from-photo; no mid-word defects
- [ ] **Lines / icons** — stroke roles, arrows, groups

## B. Automated gates (all exit 0)

```bash
python3 scripts/source_audit.py --spec work/.../spec.json --original work/.../original.png \
  --hints work/.../text_hints.json --out work/.../source_audit.json

python3 scripts/verify_pptx.py --pptx <out.pptx> --spec work/.../spec.json \
  --original work/.../original.png --out work/.../verify_report.json

python3 scripts/export_slide_png.py --pptx <out.pptx> --out work/.../render.png

python3 scripts/compare_render.py --original work/.../original.png \
  --render work/.../render.png --out work/.../compare
```

| Gate | Proves |
|------|--------|
| `source_audit` | Spec boxes hit real ink on the **photo** |
| `verify_pptx` | Shape / font / color match spec (+ probes) |
| `compare_render` | Real PowerPoint raster vs photo (cards **or** centered MAE) |

Centered / marketing UIs with no cream header cards: `compare_render` passes when **both** sides have 0 cards and pixel MAE ≤ 55 (see `layout_model: centered_composition`).

## C. Delivery statement

1. Path to `.pptx`
2. All three gates passed
3. Pre-delivery checklist (all categories) completed

## D. Local repair (standing order)

When ORIGINAL|RENDER or a user crop shows an error:

1. Identify the **smallest** failing element (one icon, one label, one line).
2. Fix only that region in `layout.json` / assets — do not rebuild the whole page unless the layout architecture is wrong.
3. Re-export, re-compare that region, append LEARNINGS if reusable.
4. See [09-job-workflow.md](09-job-workflow.md).

## Compare detector

- Prefer **row-band** colored headers (green/blue/yellow/red), not flood-fill — same-hue diagram borders must not merge into a tall “card.”
- Cream-card blob detection is the fallback for other decks.
- Fail on origin-stacked groups (`DOUBLE_OFFSET_BUG` symptom).


## D. Auto compare → learn (standing order — no user prompt needed)

After **every** rebuild (and whenever the user sends a crop / “this looks wrong” image):

1. Export + `compare_render` → open `compare_side_by_side.png` (and the user crop if any).
2. Diff **gaps, docking, wraps, colors** against the original — do not stop at “gates PASSED” if the side-by-side still shows pile-up, wrong pads, or floating lines.
3. Fix the deck.
4. Append [LEARNINGS.md](LEARNINGS.md) (`category:` + one-line rule).
5. Promote into `01`–`06` if reusable.
6. Re-run checklist A + gates B.

When `nest_detect.py` changes (or the user says “Eagle / self-test”):

```bash
python3 scripts/eagle_batch_selftest.py
```

Require `fail=0`. SKIP is OK for non-card layouts. Fix FAILs before pushing.

The user should **not** have to say “encode this” or “make it universal.” That is the default loop.
