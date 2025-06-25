#!/bin/bash
# Build external submodules (Direwolf and Hamlib)

set -e

# Absolute path to the project root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT_DIR/bin"

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

    local prefix="$ROOT_DIR/bin"

    # First build with debug CFLAGS
    ../configure CFLAGS="-g -O0"
    make -j"$(nproc)"
    make install

    # Reconfigure to install binaries to the local bin directory
    make distclean || true
    ../configure --prefix="$prefix"
    make -j"$(nproc)"
    make check
    make install

    cd ../../..
}

# Build Direwolf using CMake
build_direwolf() {
    local path="external/direwolf"
    git submodule update --init --remote "$path"
    cd "$path"
    mkdir -p build
    cd build
    cmake ..
    make -j"$(nproc)"
    cd ../../..
}

build_hamlib
build_direwolf
