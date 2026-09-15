#!/bin/bash
# One-time setup for screenshot-to-editable-pptx

echo "=== Installing dependencies ==="

# Python deps
pip3 install python-pptx svg2pptx pillow 2>/dev/null

# editppt (requires Python 3.10+)
python3.11 -m pip install --editable ~/.hermes/skills/image-to-editable-ppt/cli/ 2>/dev/null

# ppt-master skill
npx -y skills@latest add /tmp/ppt-master/skills/ppt-master --skill ppt-master --agent hermes-agent --global -y 2>/dev/null

echo "=== Setup complete ==="
echo "Next: editppt config --paddle-ocr-token <token>"
echo "      editppt config --api-key <key> --base-url <url> --model <model>"