---
name: screenshot-to-editable-pptx
description: Turn any screenshot into 100% editable, grouped, scalable PowerPoint slides. Pipeline: editppt (OCR + rebuild) → svg2pptx (icons) → ppt-master (beautify) → SYSTEM.md (verify).
---

# Screenshot → Editable PPTX

Zero-dependency pipeline for converting screenshots to editable PowerPoint slides.

## Quick Start

```bash
bash pipeline.sh <screenshot.png>
```

## Pipeline Steps

1. **Measure** — PIL pixel sampling + vision analysis (per SYSTEM.md)
2. **Rebuild** — editppt prepare → run for OCR-assisted reconstruction
3. **Icons** — svg2pptx for custom shapes
4. **Beautify** — ppt-master for templates and polish
5. **Verify** — SYSTEM.md self-check rules

## Prerequisites

- editppt CLI (with PaddleOCR token)
- python-pptx, svg2pptx
- ppt-master skill
- SiliconFlow or OpenAI API key (for image generation)