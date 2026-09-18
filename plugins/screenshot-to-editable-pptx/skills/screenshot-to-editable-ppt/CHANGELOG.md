# Changelog highlights

## 2026-09-17 — Accuracy gates (text fidelity + ROI)

- `scripts/check_text_fidelity.py` — fail if text↔text gaps collapse, one-liners wrap, or bold mismatches
- `scripts/compare_rois.py` — regional MAE so global MAE cannot hide local drift
- `scripts/detect_progress_bar.py` — grey track (back) + black fill (front)
- `mapping.font_pt_from_cap_height` + `one_line_box_width` — stop descender-inflated pt / wrap-to-fit


## 2026-09-17 — Universal measure-first enrichments

Public skill package updates for Cursor / Claude Code:

- **Five ops tools:** contact sheet, png-fallback policy, `layout.json` → `build_pptx_from_layout.py`, optional OCR string fill, per-page jobs + local repair
- **Modes:** layout vs component in one skill (`07-layout`, `08-layers`, `09-job-workflow`)
- **Text HARD rules:** always measure text↔text gaps; photo one-liners stay `wrap=False`; measure bold vs regular; cap-height → pt
- **Delivery:** no full-slide white backing shape (`set_background` only); progress bars = grey track (back) + fill (front)
- **Checklist:** category HARD items before the three automated gates

See [README.md](README.md) “What’s new” and [references/rules/LEARNINGS.md](references/rules/LEARNINGS.md).
