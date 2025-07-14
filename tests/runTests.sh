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
    if ! python3 -m venv "$VENV_DIR" 2>/dev/null; then
        # Some minimal Ubuntu/Debian installs lack the ensurepip module which
        # causes `python3 -m venv` to fail. Attempt to install the appropriate
        # python3-venv package so tests can run out of the box.
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
