# Layout JSON schema (universal assemble contract)

**Category:** `layers` / delivery  
Coordinates are always **source-image pixels**. The builder scales to slide inches.

## File: `layout.json`

```json
{
  "source_width": 1024,
  "source_height": 635,
  "slide_h_in": 7.5,
  "slide_w_in": null,
  "background": "#FFFFFF",
  "mode": "layout",
  "elements": []
}
```

`slide_w_in` optional — defaults to `slide_h_in * source_width / source_height`.

**Page background:** put the solid page color in `background` only. The builder calls `set_background(slide, …)`. **Do not** add a full-slide white (or same-as-bg) rectangle as an element — it is selectable clutter and is not needed.

## Element types

### `text` / `textbox` (Layer C)
```json
{
  "type": "text",
  "name": "headline",
  "box": [55, 283, 313, 70],
  "text": "It's easy to get\nstarted on Airbnb",
  "font_pt": 26,
  "bold": true,
  "color": "#242424",
  "align": "left",
  "wrap": true,
  "text_source": "manual|ocr|hints"
}
```
Font pt from `font_pt_from_glyph` / `text_hints` — never guessed. Optional OCR fills `text` only (`ocr_fill_text.py`).

### `shape` (Layer B)
```json
{
  "type": "shape",
  "name": "exit",
  "shape": "rounded_rect",
  "box": [953, 21, 41, 28],
  "fill": "#FFFFFF",
  "line": "#ECECEC",
  "line_pt": 0.75,
  "rad": 0.5
}
```

### `line` (Layer B)
```json
{
  "type": "line",
  "name": "div1",
  "points": [563, 249.5, 970, 249.5],
  "color": "#F1F1F1",
  "line_pt": 0.75
}
```

### `image` / `picture` (Layer A)
```json
{
  "type": "image",
  "name": "icon1",
  "box": [896, 156, 75, 63],
  "path": "assets/icon1.png",
  "png_fallback": "assets/icon1.png",
  "svg": "assets/icon1.svg"
}
```
**png-fallback policy:** if both SVG and PNG exist, the **visible** PPT object is the PNG; keep SVG in `assets/` as the vector intermediate. PowerPoint often mishandles SVG with embedded rasters/filters.

## z-order

List order = paint order. Typical: large panels → Layer A images → lines → text.  
(Solid page color is `layout.background`, not an element.)

## Multi-page

One `pages/page_NNN/layout.json` per page. Build each, then merge slides in PowerPoint / a finalize step. See [09-job-workflow.md](09-job-workflow.md).

## Builder

```bash
python3 scripts/build_pptx_from_layout.py \\
  --layout pages/page_001/layout.json \\
  --assets-root pages/page_001 \\
  --out pages/page_001/page.pptx
```
