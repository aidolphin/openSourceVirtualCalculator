#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3.11}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_FALLBACK:-python3}"
fi

echo "Using Python: $("$PYTHON_BIN" --version)"

if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

if ! ".venv/bin/python" -c "import cv2, mediapipe, numpy" >/dev/null 2>&1; then
  echo "Installing dependencies from requirements.txt..."
  ".venv/bin/python" -m pip install --upgrade pip
  ".venv/bin/python" -m pip install -r requirements.txt
else
  echo "Dependencies already installed; skipping pip install."
fi

".venv/bin/python" hand_calculator_v2.py
