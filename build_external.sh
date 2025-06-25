#!/bin/bash
# Build external submodules (Direwolf and Hamlib) without installing

set -e

# Build Hamlib using autotools
build_hamlib() {
    local path="external/hamlib"
    git submodule update --init --remote "$path"
    cd "$path"
    ./bootstrap
    mkdir -p build
    cd build
    ../configure
    make -j"$(nproc)"
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
