#!/bin/bash
# Build external submodules (Direwolf and Hamlib)

set -e

# Absolute path to the project root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure autoconf, automake and libtool are available
ensure_autotools() {
    if command -v autoreconf >/dev/null 2>&1 \
        && command -v automake >/dev/null 2>&1 \
        && command -v libtool >/dev/null 2>&1; then
        return
    fi
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y autoconf automake libtool
    else
        echo "Missing autoreconf, automake or libtool" >&2
        echo "Please install the GNU autotools before building Hamlib" >&2
        exit 1
    fi
}

# Build Hamlib using autotools
build_hamlib() {
    ensure_autotools
    local path="external/hamlib"
    git submodule update --init --remote "$path"
    cd "$path"
    ./bootstrap
    mkdir -p build
    cd build

    # Configure and build Hamlib without installing it. The rigctld binary will
    # remain under the build/tests directory.
    ../configure CFLAGS="-g -O0"
    make -j"$(nproc)"
    make check

    cd ../../..
}

# Build Direwolf using CMake
build_direwolf() {
    local path="external/direwolf"
    git submodule update --init --remote "$path"
    cd "$path"
    mkdir -p build
    cd build
    local hamlib_root="$ROOT_DIR/external/hamlib/build"
    cmake .. -DHAMLIB_ROOT_DIR="$hamlib_root"
    make -j"$(nproc)"
    cd ../../..
}

build_hamlib
build_direwolf
