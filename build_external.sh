#!/bin/bash
# Build external submodules (Direwolf and Hamlib)

set -e

# Absolute path to the project root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT_DIR/bin" "$ROOT_DIR/include" "$ROOT_DIR/lib"

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

    # Install Hamlib directly under the project root so libraries and
    # headers land in "lib" and "include/hamlib". This avoids writing to
    # system directories like /usr/local.
    local prefix="$ROOT_DIR"
    local libdir="$prefix/lib"
    local includedir="$prefix/include"

    # First build with debug CFLAGS
    ../configure --prefix="$prefix" --libdir="$libdir" --includedir="$includedir" CFLAGS="-g -O0"
    make -j"$(nproc)"
    make install

    # Reconfigure to install binaries to the local prefix with release flags
    make distclean || true
    ../configure --prefix="$prefix" --libdir="$libdir" --includedir="$includedir"
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
