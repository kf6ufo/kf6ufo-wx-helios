#!/usr/bin/env bash
# Launch wx-helios using the project's Python environment.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer local virtual environment if present
if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/venv/bin/python"
elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

exec "$PYTHON" "$SCRIPT_DIR/main.py" "$@"

