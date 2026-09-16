# Walkthrough — 2×2 pattern cards

This is the reconstruction loop used on the “AI agent design patterns” screenshot in the parent lab folder. Same loop applies to any slide.

## 1. Analyze

Visible structure:

- White slide, rounded outer frame
- Centered title
- Four cards: Single (green), Sequential (blue), Parallel (yellow), Hierarchical (red)
- Each card: colored header bar, node diagram, caption
- Soft card shadows; diagrams themselves are flat

## 2. Sample color (never guess)

```bash
python3 scripts/pil_sampler.py \
  --image Screenshot.png \
  --regions "bg:20,20,40,40 single:200,220,80,30 sequential:700,220,80,30 parallel:200,520,80,30 hierarchical:700,520,80,30" \
  --out work/colors.json
```

Expected brand fills (confirm against the JSON, do not hard-code blindly):

- Single `#34A853`
- Sequential `#4285F4`
- Parallel `#FBBC04`
- Hierarchical `#EA4335`

Put each into `spec.json` `color_probes` with the pixel that was sampled.

## 3. Measure

Treat the outer frame as the container. Convert title, four cards, header bars, and captions to `%` with `proportion_chain.py`. Copy `slide_pct` into each spec element.

Measure every text line first:

```bash
python3 scripts/text_hints.py \
  --image Screenshot.png \
  --out work/text_hints.json \
  --overlay work/text_hints.png
```

Title ~glyph-measured pt (text_hints size_group 0). Header labels share the next group. Captions share the smallest. Lock those sizes from `text_hints.json`, not from a guess. One spec text element per visual line.

## 4. Build

Bottom → top: background, frame, four cards (header, body, diagram ovals/rects, caption), group each card.

Icons/nodes = `OVAL`. Header = `ROUNDED_RECTANGLE` plus a 2-pt strip to square off the bottom corners.

## 5. Verify before sending

```bash
python3 scripts/source_audit.py \
  --spec work/spec.json --original Screenshot.png \
  --hints work/text_hints.json --out work/source_audit.json
python3 scripts/pptx_inspect.py --pptx rebuilt.pptx --out work/inspect.json
python3 scripts/verify_pptx.py \
  --pptx rebuilt.pptx \
  --spec work/spec.json \
  --original Screenshot.png \
  --out work/verify_report.json
python3 scripts/export_slide_png.py --pptx rebuilt.pptx --out work/render.png
python3 scripts/compare_render.py \
  --original Screenshot.png --render work/render.png --out work/compare
```

Send the file only when source-audit, shape/font/color, and the PowerPoint raster all print `PASSED`.
