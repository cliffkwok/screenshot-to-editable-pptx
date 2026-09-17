#!/usr/bin/env python3
"""Init a universal per-page job directory for screenshot → editable PPT.

Layout:
  work/<job>/
    deck_manifest.json
    pages/page_001/
      source.png          # copy or symlink of page raster
      _layers.json
      layout.json
      assets/
      compare/
      qa_report.md
    final/                # after finalize

Usage:
  python3 scripts/init_job.py --job work/my-deck --images shot1.png shot2.png
  python3 scripts/init_job.py --job work/my-deck --image shot.png --name page_001
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


QA_STUB = """# QA report — page {page}

## Mode
- [ ] layout / component (inferred or overridden)

## Layers
- [ ] A/B/C inventory complete (`_layers.json`)
- [ ] Layer A contact sheet reviewed (`assets/_contact_sheet.png`)
- [ ] png-fallback used where SVG would break PPT

## Fidelity
- [ ] ORIGINAL|RENDER side-by-side checked
- [ ] Local repair only (no full-page rebuild unless layout plan wrong)

## Known limits
- (list regions that must stay Layer A pictures)
"""


def init_page(page_dir: Path, source: Path, page_id: str) -> dict:
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "assets").mkdir(exist_ok=True)
    (page_dir / "compare").mkdir(exist_ok=True)
    dest = page_dir / "source.png"
    if source.resolve() != dest.resolve():
        shutil.copy2(source, dest)
    qa = page_dir / "qa_report.md"
    if not qa.exists():
        qa.write_text(QA_STUB.format(page=page_id))
    return {
        "id": page_id,
        "dir": str(page_dir),
        "source": str(dest),
        "status": "ready",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--job", required=True, help="job root under work/")
    ap.add_argument("--images", nargs="*", default=[], help="one or more page rasters")
    ap.add_argument("--image", default="", help="single image")
    ap.add_argument("--name", default="page_001")
    args = ap.parse_args()

    job = Path(args.job)
    job.mkdir(parents=True, exist_ok=True)
    (job / "final").mkdir(exist_ok=True)
    (job / "pages").mkdir(exist_ok=True)

    images = list(args.images)
    if args.image:
        images = [args.image] + images
    if not images:
        print("ERROR: pass --image or --images")
        sys.exit(1)

    pages = []
    for i, img in enumerate(images, start=1):
        src = Path(img)
        if not src.exists():
            print(f"ERROR: missing {src}")
            sys.exit(1)
        page_id = args.name if len(images) == 1 else f"page_{i:03d}"
        page_dir = job / "pages" / page_id
        pages.append(init_page(page_dir, src, page_id))
        print(f"  {page_id} ← {src}")

    manifest = {
        "job": str(job),
        "created": datetime.now(timezone.utc).isoformat(),
        "page_count": len(pages),
        "pages": pages,
        "workflow": [
            "1. mode + layers inventory per page",
            "2. Layer A crops → contact_sheet.py",
            "3. measure B/C → layout.json",
            "4. optional ocr_fill_text.py",
            "5. build_pptx_from_layout.py",
            "6. gates + ORIGINAL|RENDER; local repair only",
            "7. finalize multi-page into final/",
        ],
    }
    path = job / "deck_manifest.json"
    path.write_text(json.dumps(manifest, indent=2))
    print(f"wrote {path} ({len(pages)} pages)")


if __name__ == "__main__":
    main()
