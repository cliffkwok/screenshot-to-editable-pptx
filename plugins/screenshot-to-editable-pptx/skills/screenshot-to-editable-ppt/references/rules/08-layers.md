# 08 — Layers (visual / structure / content)

**Category tag:** `layers`  
**When to update:** complex icons forced into crude shapes, text baked into images, missed small visuals, full-slide screenshot paste, SVG that PPT drops.

## Law

> Decompose every screenshot into **three layers** before building.  
> Prefer native editable objects. Use a picture asset only when native shapes cannot match the photo.

## Layers

| Layer | Contains | Implementation | Editable? |
|-------|----------|----------------|-----------|
| **A — Visual assets** | Complex illustrations, photos, 3D icons, textures | See **Layer A policy** | Replaceable picture (+ optional SVG file) |
| **B — Structure** | Cards, panels, dividers, arrows, badges, chrome | Native PPT shapes / lines | Fully editable |
| **C — Content** | All readable text | Native text boxes | Fully editable |

**Never** bake Layer C text into a Layer A image. **Never** paste the full screenshot as the slide.

## Layer A policy (prefer in order)

1. **Native shape group** — simple motifs (doc icon, pill, flat badge). Measure pads; rebuild with primitives.
2. **Vectorize** — crop measured bbox → `scripts/vectorize_region.py` → SVG intermediate + PNG crop.
3. **Picture (png-fallback)** — place the **PNG** in PPT at the measured box. Keep SVG on disk when present.

### png-fallback (universal)

If both `icon.svg` and `icon.png` exist:
- **Visible PPT object = PNG** (`png_fallback` / `path` in layout.json)
- **SVG stays in `assets/`** as the editable/vector reference

PowerPoint often mishandles SVG with filters or embedded rasters. Do not rely on SVG as the only visible layer.

### Contact sheet (required after Layer A crops)

```bash
python3 scripts/contact_sheet.py \\
  --assets pages/page_001/assets \\
  --out pages/page_001/assets/_contact_sheet.png --label
```

Review the sheet before assemble — catch missing/cropped icons.

## Phase checklist

### Phase 1 — Inventory
1. List every element: `box_px`, role, layer `A|B|C` → `_layers.json` (`layer_inventory.py`).
2. Completeness pass: small icons, hairlines, chrome.
3. Mode: [07-layout.md](07-layout.md) vs component.

### Phase 2 — Assets (Layer A)
1. Crop / vectorize each A element.
2. Run **contact sheet**.
3. No text in any A asset.

### Phase 3 — Assemble
1. Write [layout-json.md](layout-json.md) → `build_pptx_from_layout.py`.
2. Optional: `ocr_fill_text.py` for Layer C strings (boxes/pt already measured).
3. z-order: bg → A → B → C.
4. Gates + ORIGINAL|RENDER. **Local repair** only ([09-job-workflow.md](09-job-workflow.md)).

## Fail patterns

| Failure | Prevention |
|---------|------------|
| New template | Positions from photo only |
| Crude over-native complex art | Layer A picture/vectorize |
| Text in images | Layer C only |
| Missed icons | Contact sheet + completeness |
| SVG blank in PPT | png-fallback |
| Full-slide PNG | Forbidden |

## Tools

- `scripts/vectorize_region.py` — crop + optional vtracer SVG
- `scripts/contact_sheet.py` — Layer A QA sheet
- `scripts/layer_inventory.py` — validate `_layers.json`
- `scripts/ocr_fill_text.py` — optional OCR strings onto measured boxes
- `scripts/build_pptx_from_layout.py` — assemble from layout.json
- `scripts/init_job.py` — per-page job directories
