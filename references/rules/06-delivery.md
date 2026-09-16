# 06 — Delivery

**Category tag:** `delivery`  
**When to update:** new gate, new checklist item, “don’t send until…”, compare detector improvements.

## Law

> Do **not** give the user a `.pptx` path, open the file, or say “done” until checklist **A** and gates **B** all pass. Statement **C** is required on delivery.

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
| `compare_render` | Real PowerPoint raster vs photo (cards, no origin stack) |

## C. Delivery statement

1. Path to `.pptx`
2. All three gates passed
3. Pre-delivery checklist (all categories) completed

## Compare detector

- Prefer **row-band** colored headers (green/blue/yellow/red), not flood-fill — same-hue diagram borders must not merge into a tall “card.”
- Cream-card blob detection is the fallback for other decks.
- Fail on origin-stacked groups (`DOUBLE_OFFSET_BUG` symptom).


1. You correct one thing → agent tags **category**.
2. Append to [LEARNINGS.md](LEARNINGS.md).
3. Promote the reusable line into `01`–`06`.
4. Re-run checklist A + gates B on the current deck.
5. Next screenshot already inherits the rule — you should not need to repeat it.
