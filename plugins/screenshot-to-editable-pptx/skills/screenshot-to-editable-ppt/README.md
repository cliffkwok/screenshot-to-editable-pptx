# Screenshot → Editable PowerPoint

> Paste a **slide screenshot**. Get a **native editable `.pptx`** — real shapes, real text, grouped icons. Not a pasted picture.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![python-pptx](https://img.shields.io/badge/python--pptx-native%20shapes-blue)](#)
[![Gates](https://img.shields.io/badge/gates-source%20%7C%20verify%20%7C%20compare-success)](#three-gates-before-delivery)

<p align="center">
  <img src="docs/assets/compare-side-by-side.png" alt="Original screenshot vs rebuilt editable PowerPoint" width="900" />
</p>

<p align="center"><em>Left: original screenshot · Right: PowerPoint slideshow raster of the rebuilt editable deck</em></p>

---

## Why this exists

Most “screenshot to PPT” tools embed the image. That looks fine until you need to edit a word, recolor a card, or move an icon.

This skill rebuilds the slide with **object-level PowerPoint shapes** and refuses to deliver until automated gates say the rebuild matches the photo.

## Features

- **Native shapes + text** — rectangles, rounds, connectors, grouped icons; never a full-slide screenshot paste
- **Glyph-box font sizing** — point size from ink height, not a guessed `pt`
- **One text box per visual line** — no multi-line wrap guessing
- **Measured bold** — stem contrast decides weight; no assumed bold
- **Attached connectors** — OOXML `stCxn` / `endCxn` when lines should stick to shapes
- **Meaningful grouping** — one group per card / icon / badge; local children, `chOff=(0,0)`
- **Fail-closed delivery** — three gates must pass before the agent sends the file

## Three gates before delivery

| Gate | Script | What it checks |
|------|--------|----------------|
| **Source** | `source_audit.py` | Spec text boxes sit on real ink in the **original** photo; glyph height matches declared pt |
| **Structure** | `verify_pptx.py` | Shape type/size/position, font name/size/weight/color, sampled fill colors |
| **Visual** | `compare_render.py` | **Real PowerPoint slideshow raster** vs original (card IoU, no origin-stacked groups) |

XML that “looks right” is not enough. PowerPoint must draw it correctly.

## Install

### Cursor

```bash
git clone https://github.com/cliffkwok/screenshot-to-editable-pptx.git
mkdir -p ~/.cursor/skills
ln -s "$(pwd)/screenshot-to-editable-pptx" ~/.cursor/skills/screenshot-to-editable-ppt
pip3 install -r requirements.txt
```

Optional project rule (always-on reminder): copy `.cursor/rules/screenshot-to-editable-ppt.mdc` into your project’s `.cursor/rules/`.

### Claude Code (plugin marketplace)

```text
/plugin marketplace add https://github.com/cliffkwok/screenshot-to-editable-pptx
/plugin install screenshot-to-editable-pptx@screenshot-to-editable-pptx
```

Then invoke the skill when you paste a screenshot and ask for an editable PowerPoint.

### Manual

Clone this repo and point your agent’s skills folder at it (same layout as Cursor above).

## Requirements

- Python 3 + `pip3 install -r requirements.txt` (`python-pptx`, `Pillow`, `lxml`)
- [Tesseract](https://github.com/tesseract-ocr/tesseract) CLI recommended (`eng+chi_tra`) for line detection
- **Microsoft PowerPoint on macOS** for `export_slide_png.py` / visual compare (Quick Look is not a valid render)

## Use

Paste a slide screenshot and ask:

> Rebuild this as an editable PowerPoint — shapes, fonts, and colors must match.

The agent will:

1. List every visible element (layout, shape, font, color, shape combinations)
2. Sample colors with PIL (no guessed hex)
3. Measure layout as % of a fixed 16:9 stage (13.333×7.5 in)
4. Measure each text line (`text_hints.py` → optional `text_measure.py`)
5. Rebuild with native shapes + one text box per line
6. Run **source_audit → verify_pptx → export → compare_render**
7. Deliver the `.pptx` **only** if all three reports show `"passed": true`

After **any** edit: rebuild and re-run all three gates.

## Verify locally

```bash
python3 scripts/text_hints.py --image screenshot.png --out text_hints.json --overlay text_hints.png
python3 scripts/source_audit.py --spec spec.json --original screenshot.png --hints text_hints.json --out source_audit.json
python3 scripts/verify_pptx.py --pptx slide.pptx --spec spec.json --original screenshot.png --out verify_report.json
python3 scripts/export_slide_png.py --pptx slide.pptx --out render.png
python3 scripts/compare_render.py --original screenshot.png --render render.png --out compare
```

Exit `0` = pass. Exit `1` = do not deliver.

## Architecture (progressive disclosure)

The main `SKILL.md` is a workflow map. Supporting files load only when needed:

| File | Purpose | Loaded when |
|------|---------|-------------|
| `SKILL.md` | Core workflow + hard gates | Always |
| `scripts/text_hints.py` | Ink boxes + glyph→pt | Before locking text into the spec |
| `scripts/text_measure.py` | Bold / centroid | When weight or fine position is unsure |
| `scripts/text_fit.py` | Render vs original ink deltas | After a first render still drifts |
| `scripts/source_audit.py` | Spec vs original photo | Before claiming the layout is locked |
| `scripts/verify_pptx.py` | Shape / font / color | Before visual compare |
| `scripts/export_slide_png.py` + `compare_render.py` | Real PPT raster vs photo | Before delivery |
| `references/*` | Schema, methodology, OOXML notes | When stuck on accuracy details |
| `examples/walkthrough.md` | End-to-end walkthrough | Onboarding |

## Accuracy notes (what we learned from peer skills)

[frontend-slides](https://github.com/zarazhangrui/frontend-slides) is an **HTML deck authoring** skill — different product. What transfers for *accuracy*:

1. **Fail-closed after any edit** — re-verify at fixed stage size; do not trust “looks fine in XML”
2. **Progressive disclosure** — measure scripts and reference docs load on demand, not all at once
3. **Visual proof is mandatory** — side-by-side raster compare before delivery

What does **not** transfer: style presets, CSS animation packs, Vercel deploy, PPT→HTML extraction. Those solve authoring/sharing, not photo→native-PPT reconstruction.

## Layout

```
screenshot-to-editable-pptx/
├── SKILL.md
├── README.md
├── LICENSE
├── requirements.txt
├── .claude-plugin/marketplace.json
├── plugins/screenshot-to-editable-pptx/   # Claude Code plugin wrapper
├── scripts/                              # measure · build · audit · verify · compare
├── references/
├── examples/
└── docs/                                 # GitHub Pages gallery
```

## Philosophy

1. **Editable means editable** — if you can’t select the text, it isn’t done.
2. **Measure, don’t guess** — hex, inches, and pt come from pixels and glyph boxes.
3. **The photo is the source of truth** — specs that only match themselves fail `source_audit`.
4. **Gates protect the user** — the agent is not allowed to “ship and hope.”

## Credits

Built for Cursor / Claude agent workflows. Packaging patterns inspired by [@zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides).

## License

MIT — use it, modify it, share it.
