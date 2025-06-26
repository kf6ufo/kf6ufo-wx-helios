#!/usr/bin/env bash
# Run the test suite using the project's Python environment.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$REPO_DIR/.venv"
WHEEL_DIR="$REPO_DIR/tests/wheels"

# Determine requirements file. Prefer a lock file if present so the
# versions are consistent when installing from wheels.
REQ_FILE="$REPO_DIR/requirements.lock"
if [ ! -f "$REQ_FILE" ]; then
    REQ_FILE="$REPO_DIR/requirements.txt"
fi

# Create the environment if needed
if [ ! -x "$VENV_DIR/bin/python" ]; then
    python3 -m venv "$VENV_DIR"
fi

# Activate the environment so any subprocesses use its tools
source "$VENV_DIR/bin/activate"

# Install project dependencies every run to ensure tests have everything.
# If the online installation fails (for example due to lack of network
# access), try to fall back to a local wheelhouse.
install_reqs() {
    python -m pip install -r "$REQ_FILE" "$@"
}

if ! install_reqs >/dev/null 2>&1; then
    echo "Failed to install dependencies from PyPI. Attempting offline install..." >&2
    if [ -d "$WHEEL_DIR" ]; then
        install_reqs --no-index --find-links "$WHEEL_DIR" || {
            echo "Could not install required packages from $WHEEL_DIR" >&2
            exit 1
        }
    else
        echo "No local wheel directory found at $WHEEL_DIR" >&2
        exit 1
    fi
fi

# Ensure pytest is available
if ! python -m pip show pytest > /dev/null 2>&1; then
    if ! python -m pip install pytest >/dev/null 2>&1; then
        if [ -d "$WHEEL_DIR" ]; then
            python -m pip install --no-index --find-links "$WHEEL_DIR" pytest || {
                echo "pytest is not available and could not be installed" >&2
                exit 1
            }
        else
            echo "pytest is required but could not be installed" >&2
            exit 1
        fi
    fi
fi

cd "$REPO_DIR/tests"
exec pytest "$@"
