#!/usr/bin/env bash
# Launch wx-helios using the project's Python environment.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_DIR="$SCRIPT_DIR/.venv"

# Create the environment if needed and install dependencies
if [ ! -x "$VENV_DIR/bin/python" ]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Activate the environment so any subprocesses use its tools
source "$VENV_DIR/bin/activate"

exec python "$SCRIPT_DIR/main.py" "$@"

