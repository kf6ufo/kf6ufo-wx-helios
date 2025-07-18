#!/bin/bash
# Build external submodules (Direwolf and Hamlib)

set -e

# Ensure basic build tools and ALSA development headers are installed
ensure_build_deps() {
    if command -v cmake >/dev/null 2>&1 \
        && command -v make >/dev/null 2>&1 \
        && pkg-config --exists alsa; then
        return
    fi
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y build-essential cmake libasound2-dev pkg-config
    else
        echo "Missing build tools or ALSA development files" >&2
        echo "Please install cmake, pkg-config and libasound2-dev" >&2
        exit 1
    fi
}

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
    ensure_build_deps
    local path="external/hamlib"
    git submodule update --init --remote "$path"
    cd "$path"
    ./bootstrap
    mkdir -p build install
    cd build

    # Configure and build Hamlib.  Install into a local directory using
    # DESTDIR so libtool does not insist on a system prefix.
    ../configure --prefix=/usr/local CFLAGS="-g -O0"
    make -j"$(nproc)"
    make check
    make DESTDIR="$ROOT_DIR/external/hamlib/install" install

    cd ../../..
}

# Build Direwolf using CMake
build_direwolf() {
    local path="external/direwolf"
    git submodule update --init --remote "$path"
    cd "$path"
    mkdir -p build
    cd build
    local hamlib_root="$ROOT_DIR/external/hamlib/install/usr/local"
    export PKG_CONFIG_PATH="$hamlib_root/lib/pkgconfig:$PKG_CONFIG_PATH"
    cmake .. -DHAMLIB_ROOT_DIR="$hamlib_root" -DCMAKE_PREFIX_PATH="$hamlib_root"
    make -j"$(nproc)"
    make DESTDIR="$ROOT_DIR/external/direwolf/install" install
    cd ../../..
}

build_hamlib
build_direwolf
