# 02 — Color

**Category tag:** `color`  
**When to update:** wrong fill/stroke/font hex, guessed theme colors, probe mismatch vs screenshot.

## Law

> **Every** visible color is measured with an **eyedropper** (exact 1×1 pixel) —
> fill, stroke, and glyph ink are **three separate clicks**.  
> Never guess. Never average a neighborhood. Never use AA fringe.  
> Prefer the user’s macOS **Colors** panel Hex when they post it (`source: "panel"`).  
> Spec `color_probes` must include **fill and stroke** for every outlined shape.

This has failed repeatedly (title ink, checkmark ink, circle fill vs stroke, Agent
border). Treat a guessed hex as a **hard fail** even if the shape geometry is right.

## Eyedropper procedure (mandatory)

```bash
# Same idea as macOS Colors → eyedropper → Hex Color #
python3 scripts/eyedropper.py --image shot.png \
  --xy 710,82 --label agent_stroke \
  --xy 700,100 --label agent_fill \
  --out work/colors.json
```

| Role | Where to click | Reject if… |
|------|----------------|------------|
| **Fill** | Interior solid (inset ≥4px; circle `r_frac<0.5`) | Hit text, icon, or fringe |
| **Stroke** | Mid of visible border | Toward fill or toward bg (AA) |
| **Glyph ink** | Darkest letter/✓/digit pixel | Halo toward fill |

### Why colors go wrong (fix these)

1. **Guessed** “close enough” red/green instead of clicking.
2. Sampled **AA fringe** (mixed border+fill) → washed hex (e.g. `#C76665` vs true `#B45654`).
3. Used **stroke** chroma as **fill** (or the reverse).
4. Probed **only fill** in `color_probes` — stroke wrong but gate still passed.
5. Ignored user’s **Colors panel** screenshot (panel hex wins).

### User posts Colors panel

If the crop shows `Hex Color #: B45654` (or RGB sliders):

1. Copy that hex **exactly** into the build constant.
2. Probe: `{"hex":"#B45654","source":"panel","apply":"line","element":"agent"}`.
3. Do not “correct” it with a nearby PIL sample.

## Measure checklist (per shape)

For **each** shape on the photo, record all that apply:

| Role | Where to sample | Do **not** sample |
|------|-----------------|-------------------|
| **Fill** | Interior solid (rect: inset ≥4px; circle: `r_frac < 0.5`, skip glyph) | Stroke ring, AA fringe, icon mark |
| **Stroke / line** | Mid of the visible border (circle: `r_frac ≈ 0.95–1.0`) | Fill interior, outside bg |
| **Glyph ink** | Darkest quartile of the letter/✓/✕/digit pixels | Halo / AA toward fill |

Write hex into build constants **and** `color_probes` with those `px`.

### Circle / ring failure mode (seen on AI Evals step “3”)

Bright chroma often lives **only on the stroke**. A `is_blue()` / `is_green()` flood of
the bbox returns the ring; using that as `fill=` paints a solid candy circle.  
**Fix:** sample fill at interior `r_frac<0.5` (avoid the “3”); sample stroke on the ring.

### Mark / icon failure mode (✓ ✕)

Do not default mark color to white on a colored disc. Measure the mark ink — photo may
be **black** on green/red (AI Evals claims).

## Procedure

1. If a Color Picker / RGB Sliders crop shows `Hex Color #: AABBCC` → use that exact value
   and set the probe `"source": "panel"` (verify skips original-pixel AA check; still checks PPTX).
2. Else sample into `work/colors.json` (or inline constants from PIL) — **one entry per role**.
3. Prefer dark **ink** pixels for text/marks — **darkest quartile** of glyph pixels.
4. Prefer solid fill interiors for headers / boxes (avoid border AA).
5. Put every critical color in `spec.color_probes` with `hex`, `apply` (`fill` | `line` | `font`);
   include `px` for eyedropper samples, or `source: "panel"` for picker hex.
6. **Outlined shapes need two probes minimum:** fill + stroke.
7. `verify_pptx` color gate must pass (fail-closed if probes missing).

## Probes (minimum)

| Probe | Typical `px` | `apply` |
|-------|--------------|---------|
| Slide / page bg | corner outside chrome | `slide_background` (via `set_background` — **no** full-slide shape) |
| Each card / disc **fill** | interior (not stroke) | `fill` |
| Each card / disc **stroke** (if visible) | border mid | probe PPT line or document in build |
| Title / label / ✓ / ✕ ink | darkest glyph pixel | `font` |

## Forbidden

| Anti-pattern | Do instead |
|--------------|------------|
| Full-slide white rectangle “backing” on white page | `set_background(slide, hex)` only |
| Guess “white check on green” | Sample ✓ pixels |
| Use bright ring detector output as fill | Interior `r_frac<0.5` sample |
| Hard-code “close enough” brand red | Sample header interior **or** panel |
| Probe on AA fringe | Darkest ink **or** panel hex |
| Trust washed PIL over Color Picker | Panel hex (`source: "panel"`) wins |
| Probe frame chrome as “bg” | True page corner → `slide_background` |
| Theme / scheme colors | `RGBColor` only |
| One hex for fill+stroke+text | Three measured roles |

## Gate

`verify_pptx.py` → `gates.color` (re-samples original unless `source: "panel"`).
