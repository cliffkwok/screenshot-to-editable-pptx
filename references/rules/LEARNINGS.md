# Learnings log

Append-only. Each entry: date · category · one-line rule · optional deck.

When a line is promoted into `01`–`06`, mark `promoted: yes`.

---

## 2026-09-16 · text · mid-word wraps are defects

- **Deck:** AI agent design patterns  
- **Saw:** `Coordinato/r`, `Agen/t`, `solutio/n` in source PNG  
- **Rule:** Do not preserve mid-word wraps for fidelity. `wrap=False`, widen host until one line fits (+ measured pad).  
- **promoted:** yes → [04-text.md](04-text.md)

## 2026-09-16 · shape · ellipse ≠ octagon

- **Deck:** AI agent design patterns  
- **Saw:** Workspace rendered as octagon; photo is smooth ellipse  
- **Rule:** Photo ellipse/circle → `OVAL` only. Never polygon-approximate.  
- **promoted:** yes → [03-shape.md](03-shape.md)

## 2026-09-16 · shape · 3D agents need back+front

- **Deck:** AI agent design patterns  
- **Saw:** Flat blurry rects vs isometric agent blocks  
- **Rule:** 3D block = offset back plate + front face (optionally grouped).  
- **promoted:** yes → [03-shape.md](03-shape.md)

## 2026-09-16 · measure · header+diagram share outline

- **Deck:** AI agent design patterns  
- **Saw:** Tall colored header flush with card; diagram frame continues same hue  
- **Rule:** Measure header solid band and diagram body separately; don’t let body content that shares the header hue inflate `HDR_H`.  
- **promoted:** yes → [01-measure.md](01-measure.md) / [03-shape.md](03-shape.md)

## 2026-09-16 · delivery · compare cards = colored headers, not cream-only

- **Deck:** AI agent design patterns  
- **Saw:** `compare_render` found orig cards via red/yellow headers but 0 render cards when flood-fill merged header+frame into a tall blob  
- **Rule:** Detect cards with **row-band** header density (not flood-fill). Cream is fallback. Same-hue diagram borders must not swallow the header bar.  
- **promoted:** yes → [06-delivery.md](06-delivery.md) + `scripts/compare_render.py`

## 2026-09-16 · color · probe ink not AA fringe

- **Deck:** AI agent design patterns  
- **Saw:** Title probe `#4F4F4F` (fringe) vs PPT `#1A1A1A`  
- **Rule:** Sample darkest glyph pixel for font probes; page corner for bg — not frame chrome.  
- **promoted:** yes → [02-color.md](02-color.md)

## 2026-09-16 · delivery · checklist before any user-facing output

- **Rule:** Pre-delivery checklist (all categories) + three gates before path/“done”.  
- **promoted:** yes → [06-delivery.md](06-delivery.md)
