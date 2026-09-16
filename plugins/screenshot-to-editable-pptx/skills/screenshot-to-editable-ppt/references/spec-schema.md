# spec.json schema

`work/spec.json` is the contract `verify_pptx.py` diffs against the PPTX. Incomplete spec → fail closed.

```json
{
  "slide": {
    "width_in": 13.33,
    "height_in": 7.5,
    "background": "#FFFFFF"
  },
  "source": {
    "width_px": 1024,
    "height_px": 576,
    "fit": "height"
  },
  "allow_pictures": false,
  "groups_required": true,
  "color_probes": [
    {
      "name": "single_header",
      "hex": "#34A853",
      "px": [420, 310],
      "apply": "fill",
      "text": "Single"
    }
  ],
  "elements": [
    {
      "name": "title",
      "kind": "text",
      "shape_type": "textbox",
      "text": "AI agent design patterns",
      "font_name": "Arial",
      "font_size_pt": 38,
      "font_size_source": "measured",
      "box_px": [160, 42, 704, 38],
      "glyph_height_px": 32,
      "size_group": 0,
      "bold": true,
      "color": "#202020",
      "align": "center",
      "x_pct": 15.0,
      "y_pct": 6.4,
      "w_pct": 70.0,
      "h_pct": 8.0,
      "has_shadow": false
    },
    {
      "name": "single_header",
      "kind": "shape",
      "shape_type": "rounded_rectangle",
      "fill": "#34A853",
      "radius": 0.04,
      "x_pct": 8.5,
      "y_pct": 17.0,
      "w_pct": 40.0,
      "h_pct": 4.3,
      "has_shadow": false
    }
  ]
}
```

## Fields

### slide

| Field | Required | Notes |
|-------|----------|--------|
| `width_in` | yes | Default 13.33 |
| `height_in` | yes | Default 7.5 |
| `background` | yes | PIL-sampled hex |

### source

Optional but required for a reliable `source_audit.py` mapping.

| Field | Required | Notes |
|-------|----------|--------|
| `width_px` `height_px` | for audit | Original screenshot size |
| `fit` | no | `height` (default, Fit-to-Window), `width`, or `stretch` |

### color_probes

At least one probe. Each probe:

| Field | Required | Notes |
|-------|----------|--------|
| `name` | yes | Label in the report |
| `hex` | yes | From `pil_sampler.py`, not Vision |
| `px` | yes if `--original` | `[x, y]` on the screenshot so verify can re-sample |
| `apply` | no | `fill` (default) or `font` |
| `text` | no | Bind probe to the shape that contains this text |
| `element` | no | Bind by spec element name |

A probe fails if:

1. Re-sampled screenshot pixel is more than ±2 RGB from `hex` (guessed color)
2. Matching PPT fill/font is more than ±2 RGB from `hex` (wrong build color)

### elements

One object per visible thing (shape or text).

| Field | Required | Notes |
|-------|----------|--------|
| `name` | yes | Unique id |
| `kind` | yes | `shape` / `text` / `textbox` |
| `shape_type` | yes for shapes | `rounded_rectangle`, `rectangle`, `circle`, `oval`, `pill`, `triangle`, `textbox` |
| `text` | yes for text | Exact visible string |
| `font_name` | yes for text | e.g. `Arial` |
| `font_size_pt` | yes for text | Number from `text_hints.py` size_group, ±1 pt tolerance |
| `font_size_source` | yes for text | `measured` (from glyph box) or `guessed` (audit warns) |
| `box_px` | no | `[x,y,w,h]` ink box on the screenshot |
| `glyph_height_px` | no | Measured ink height used to derive pt |
| `size_group` | no | Shared type level (0 = largest) |
| `bold` | yes for text | boolean |
| `color` | yes for text | Hex |
| `x_pct` `y_pct` `w_pct` `h_pct` | yes | Percent of **slide** (0–100), ±3% |
| `radius` | rounded / pill | 0.03–0.08 small, 0.15–0.25 large, 0.5 pill |
| `has_shadow` | yes | boolean from Vision pass B |
| `is_circle` | circles | true → width must equal height |
| `fill` | filled shapes | Hex (also list in `color_probes`) |

`kind: "text"` still participates in the **shape** gate (position/size) and the **font** gate. One spec text element per visual line. Do not put two screenshot lines in one wrapped box.

`source_audit.py` additionally fails a text element when the mapped box has no ink on the original, glyph height is off the declared pt (ratio outside 0.75–1.35), or the box misses a measured `text_hints` line (IoU < 0.15).

## Tolerances (locked)

| Check | Tolerance |
|-------|-----------|
| Color | ±2 per RGB channel |
| Font size | ±1 pt in XML; glyph-height ratio 0.75–1.35 vs original |
| Position / size | ±3% of slide |
| Radius | ±0.08 |
| Bold / type / text | exact |
