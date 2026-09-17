#!/usr/bin/env python3
"""Batch nest_detect self-test against an Eagle .library (Master Layout default).

Usage:
  python3 scripts/eagle_batch_selftest.py
  python3 scripts/eagle_batch_selftest.py --library "/path/to/Foo.library"
  python3 scripts/eagle_batch_selftest.py --fail-on-skip   # treat SKIP as failure

Writes work/eagle-batch/batch_report.json + per-image nest/overlay.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIB = Path(
    "/Users/admin/Synology_Home/Eagles Library/Master Layout.library"
)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--library", type=Path, default=DEFAULT_LIB)
    ap.add_argument("--out", type=Path, default=ROOT / "work" / "eagle-batch")
    ap.add_argument("--fail-on-skip", action="store_true")
    args = ap.parse_args()

    images = args.library / "images"
    if not images.is_dir():
        print(f"ERROR: no images/ under {args.library}")
        sys.exit(2)

    out = args.out
    (out / "nests").mkdir(parents=True, exist_ok=True)
    (out / "overlays").mkdir(parents=True, exist_ok=True)
    script = ROOT / "scripts" / "nest_detect.py"

    results = []
    for info in sorted(images.glob("*.info")):
        meta_path = info / "metadata.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        if meta.get("isDeleted"):
            continue
        name = meta.get("name") or info.stem
        imgs = [
            p for p in info.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
            and "thumbnail" not in p.name.lower()
        ]
        if not imgs:
            results.append({"id": info.stem, "name": name, "status": "NO_IMAGE"})
            continue
        img = imgs[0]
        nest_out = out / "nests" / f"{info.stem}.json"
        overlay = out / "overlays" / f"{info.stem}.png"
        proc = subprocess.run(
            [
                sys.executable, str(script),
                "--image", str(img),
                "--out", str(nest_out),
                "--overlay", str(overlay),
                "--self-test",
            ],
            capture_output=True, text=True,
        )
        status = "FAIL"
        layout = None
        n_cards = 0
        msgs = []
        if nest_out.exists():
            data = json.loads(nest_out.read_text())
            layout = data.get("layout_kind")
            n_cards = len(data.get("cards") or [])
        # parse self-test line from stdout
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if "SELF-TEST PASS" in text:
            status = "PASS"
        elif "SELF-TEST SKIP" in text:
            status = "SKIP"
        elif "SELF-TEST FAIL" in text:
            status = "FAIL"
            for line in text.splitlines():
                if line.strip().startswith("- "):
                    msgs.append(line.strip()[2:])
        else:
            status = "FAIL"
            msgs.append(f"rc={proc.returncode}")

        row = {
            "id": info.stem,
            "name": name,
            "w": meta.get("width"),
            "h": meta.get("height"),
            "status": status,
            "layout_kind": layout,
            "n_cards": n_cards,
            "messages": msgs,
        }
        results.append(row)
        print(f"{status:4s}  cards={n_cards}  layout={layout!s:12s}  {name[:55]}")

    report = {
        "library": str(args.library),
        "n": len(results),
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "fail": sum(1 for r in results if r["status"] == "FAIL"),
        "skip": sum(1 for r in results if r["status"] == "SKIP"),
        "results": results,
    }
    (out / "batch_report.json").write_text(json.dumps(report, indent=2))
    print(
        f"\n=== SUMMARY pass={report['pass']} fail={report['fail']} "
        f"skip={report['skip']} total={report['n']} ==="
    )
    print(f"report: {out / 'batch_report.json'}")

    if report["fail"]:
        sys.exit(1)
    if args.fail_on_skip and report["skip"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
