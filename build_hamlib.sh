#!/bin/bash
# Build the wx-helios-hamlib submodule without installing

set -e

# Initialize submodule if needed
if [ ! -d "external/hamlib" ] || [ ! -d "external/hamlib/.git" ]; then
    git submodule update --init external/hamlib
fi

cd external/hamlib
mkdir -p build
cd build
cmake ..
make -j$(nproc)
