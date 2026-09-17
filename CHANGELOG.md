# Changelog highlights

## 2026-09-17 — Universal measure-first enrichments

Public skill package updates for Cursor / Claude Code:

- **Five ops tools:** contact sheet, png-fallback policy, `layout.json` → `build_pptx_from_layout.py`, optional OCR string fill, per-page jobs + local repair
- **Modes:** layout vs component in one skill (`07-layout`, `08-layers`, `09-job-workflow`)
- **Text HARD rules:** always measure text↔text gaps; photo one-liners stay `wrap=False`; measure bold vs regular; cap-height → pt
- **Delivery:** no full-slide white backing shape (`set_background` only); progress bars = grey track (back) + fill (front)
- **Checklist:** category HARD items before the three automated gates

See [README.md](README.md) “What’s new” and [references/rules/LEARNINGS.md](references/rules/LEARNINGS.md).
