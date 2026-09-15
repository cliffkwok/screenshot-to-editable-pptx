#!/bin/bash
# Screenshot → Editable PPTX Pipeline v2
# Integrates: editppt (OCR) + python-pptx (reconstruct) + SYSTEM.md (verify)
# Usage: bash pipeline.sh <project_name> <screenshot.png>

set -e

PROJECT="${1:?Usage: bash pipeline.sh <project_name> <screenshot.png>}"
SCREENSHOT="${2:?Usage: bash pipeline.sh <project_name> <screenshot.png>}"

BASE="$(cd "$(dirname "$0")" && pwd)"
PROJ="$BASE/projects/$PROJECT"
mkdir -p "$PROJ/sources" "$PROJ/output"

echo "╔══════════════════════════════════════╗"
echo "║  Screenshot → Editable PPTX v2     ║"
echo "╚══════════════════════════════════════╝"
echo "Project: $PROJECT"
echo "Source:  $SCREENSHOT"

# Step 1: Copy source
echo ""
echo "[1/4] Copying source image..."
cp "$SCREENSHOT" "$PROJ/sources/original.png"

# Step 2: OCR + text hints (editppt)
echo "[2/4] editppt OCR analysis..."
editppt prepare "$SCREENSHOT" 2>&1 | tail -3

# Step 3: Reconstruct (python-pptx + SYSTEM.md rules)
echo "[3/4] Reconstructing using SYSTEM.md rules..."
PYTHON_SCRIPT="$PROJ/reconstruct.py"
if [ -f "$PYTHON_SCRIPT" ]; then
    python3 "$PYTHON_SCRIPT"
else
    echo "  ⚠ No reconstruct.py found — create one per SYSTEM.md rules"
fi

# Step 4: Verify (SYSTEM.md)
echo "[4/4] SYSTEM.md verification..."
python3 "$BASE/scripts/selfcheck.py" "$PROJ/output/"*.pptx 2>/dev/null || echo "  ⚠ Manual Step 10 diff recommended"

echo ""
echo "=== Pipeline Complete ==="
echo "Output: $PROJ/output/"
ls "$PROJ/output/" 2>/dev/null || echo "  Check project directory"