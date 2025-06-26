#!/usr/bin/env bash
# Run the test suite using the project's Python environment.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$REPO_DIR/.venv"

# Create the environment if needed and install dependencies
if [ ! -x "$VENV_DIR/bin/python" ]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install -r "$REPO_DIR/requirements.txt"
fi

# Activate the environment so any subprocesses use its tools
source "$VENV_DIR/bin/activate"

# Ensure pytest is available
if ! python -m pip show pytest > /dev/null 2>&1; then
    python -m pip install pytest
fi

cd "$REPO_DIR/tests"
exec pytest "$@"
