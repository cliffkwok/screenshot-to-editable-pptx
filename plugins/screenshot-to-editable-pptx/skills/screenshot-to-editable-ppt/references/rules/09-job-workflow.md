# 09 — Job workflow (multi-page + local repair)

**Category tag:** `delivery`  
**When to update:** multi-page packaging, finalize order, repair scope.

## Law

> One **job directory** per conversion. Per-page isolation. **Repair the smallest failing region** — do not rebuild the whole page unless the layout plan is wrong.

## Job tree

```text
work/<job-id>/
├── deck_manifest.json
├── pages/
│   └── page_001/
│       ├── source.png
│       ├── _layers.json
│       ├── layout.json
│       ├── assets/              # Layer A crops (+ optional .svg)
│       │   └── _contact_sheet.png
│       ├── compare/
│       ├── qa_report.md
│       ├── page.pptx
│       └── render.png
└── final/
    └── <name>.pptx
```

Init:

```bash
python3 scripts/init_job.py --job work/my-deck --images s1.png s2.png
```

## Per-page pipeline (universal)

1. **Mode** — layout vs component ([07-layout.md](07-layout.md))
2. **Layers** — A/B/C inventory ([08-layers.md](08-layers.md))
3. **Layer A** — crop measured boxes → `vectorize_region.py` (SVG if available) → **always** PNG → `contact_sheet.py`
4. **Measure B/C** — pads, strokes, glyph→pt → write `layout.json` ([layout-json.md](layout-json.md))
5. **Optional OCR** — `ocr_fill_text.py` fills `text` only; does not move boxes or invent pt
6. **Assemble** — `build_pptx_from_layout.py`
7. **Gates** — source_audit / verify / export / compare_render + ORIGINAL|RENDER
8. **Local repair** — fix only failing elements; re-export; re-compare that region

## Local repair rule

| Symptom | Repair scope |
|---------|----------------|
| One icon wrong | Re-crop / replace that Layer A asset |
| One label pt/wrap | Edit that text element in layout.json |
| One divider weight | That line’s `line_pt` only |
| Whole columns shifted | Re-measure layout plan (broader OK) |

Do **not** regenerate the entire page because one asset failed.

## Finalize (multi-page)

Build each `page.pptx`, then combine into `final/` (python-pptx append slides, or open and copy slides in PowerPoint). Preserve page order from `deck_manifest.json`.

## QA artifacts (required)

- `assets/_contact_sheet.png` — Layer A completeness
- `compare/compare_side_by_side.png` or `eye_*_sbs.png`
- `qa_report.md` — regions that must remain pictures
