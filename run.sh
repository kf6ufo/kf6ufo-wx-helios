#!/usr/bin/env bash
# Launch wx-helios using the project's Python environment.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_DIR="$SCRIPT_DIR/.venv"

# Create the environment if needed and install dependencies
if [ ! -x "$VENV_DIR/bin/python" ]; then
    if ! python3 -m venv "$VENV_DIR" 2>/dev/null; then
        # Some minimal Ubuntu/Debian installs lack the ensurepip module which
        # causes `python3 -m venv` to fail. Attempt to install the appropriate
        # python3-venv package so the program can run out of the box.
        if command -v apt-get >/dev/null; then
            PY_VENV_PKG="python$(python3 -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')-venv"
            echo "Installing $PY_VENV_PKG to enable Python virtual environments..."
            if command -v sudo >/dev/null; then
                sudo apt-get update && sudo apt-get install -y "$PY_VENV_PKG"
            else
                apt-get update && apt-get install -y "$PY_VENV_PKG"
            fi
            rm -rf "$VENV_DIR"
            python3 -m venv "$VENV_DIR"
        else
            echo "Failed to create Python virtual environment and automatic installation is not available." >&2
            echo "Please install the appropriate python3-venv package for your system." >&2
            exit 1
        fi
    fi
    "$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Activate the environment so any subprocesses use its tools
source "$VENV_DIR/bin/activate"

cd "$SCRIPT_DIR"
exec python "$SCRIPT_DIR/main.py" "$@"

