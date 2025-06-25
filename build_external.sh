#!/bin/bash
# Build external submodules (Direwolf and Hamlib) without installing

set -e

# Function to build a submodule
build_module() {
    local path="$1"
    git submodule update --init --remote "$path"
    cd "$path"
    mkdir -p build
    cd build
    cmake ..
    make -j$(nproc)
    cd ../../..
}

build_module external/hamlib
build_module external/direwolf
