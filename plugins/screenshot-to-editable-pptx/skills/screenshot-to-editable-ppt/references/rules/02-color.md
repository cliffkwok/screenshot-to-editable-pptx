# 02 — Color

**Category tag:** `color`  
**When to update:** wrong fill/stroke/font hex, guessed theme colors, probe mismatch vs screenshot.

## Law

> Never guess hex. PIL-sample the screenshot at measured `(x,y)`.  
> Spec `color_probes` must match **both** the original sample **and** the PPTX fill/font.

## Procedure

1. Sample into `work/colors.json` (or inline constants from PIL).
2. Prefer dark **ink** pixels for text (avoid anti-aliased gray edges).
3. Prefer solid fill interiors for headers / boxes (avoid border AA).
4. Put every critical color in `spec.color_probes` with `px`, `hex`, `apply` (`fill` | `font`).
5. `verify_pptx` color gate must pass (fail-closed if probes missing).

## Probes (minimum)

| Probe | Typical `px` | `apply` |
|-------|--------------|---------|
| Slide / page bg | corner outside chrome | `fill` → `slide_bg` |
| Each card header | mid of solid bar | `fill` |
| Title ink | darkest glyph pixel | `font` |

## Forbidden

| Anti-pattern | Do instead |
|--------------|------------|
| Hard-code “close enough” brand red | Sample header interior |
| Probe on AA fringe (`#4F4F4F` title edge) | Darkest ink pixel |
| Probe on frame chrome as “bg” | True page corner / named `slide_bg` |
| Theme / scheme colors | `RGBColor` only |

## Gate

`verify_pptx.py` → `gates.color`.
