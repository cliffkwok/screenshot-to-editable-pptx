#!/bin/bash
# Screenshot → Editable PPTX Pipeline
# Usage: bash pipeline.sh <screenshot.png>

set -e

SCREENSHOT="${1:?Usage: bash pipeline.sh <screenshot.png>}"
NAME=$(basename "$SCREENSHOT" | sed 's/\.[^.]*$//')
OUTDIR="output/${NAME}"
mkdir -p "$OUTDIR"

echo "=== Pipeline: Screenshot → Editable PPTX ==="
echo "Input: $SCREENSHOT"

# Step 1: Prepare with editppt (OCR + structure)
echo "[1/4] editppt prepare..."
editppt prepare "$SCREENSHOT" --out "$OUTDIR"

# Step 2: Rebuild pages
echo "[2/4] editppt run..."
cd "$OUTDIR"
RUN_DIR=$(ls -d run_* 2>/dev/null | head -1)
if [ -n "$RUN_DIR" ]; then
  while true; do
    STATUS=$(editppt run next "$RUN_DIR" 2>&1)
    echo "$STATUS"
    if echo "$STATUS" | grep -q "complete\|finalize"; then
      break
    fi
  done
  editppt run finalize "$RUN_DIR"
fi
cd - > /dev/null

# Step 3: Verify with SYSTEM.md rules
echo "[3/4] SYSTEM.md verify..."
python3 scripts/verify.py "$OUTDIR"

# Step 4: Beautify with ppt-master (if skill available)
echo "[4/4] ppt-master beautify..."
echo "  → Ready for manual beautify: $OUTDIR"

echo "=== Done: $OUTDIR ==="