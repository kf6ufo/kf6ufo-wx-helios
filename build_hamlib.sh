#!/bin/bash
# Build the wx-helios-hamlib submodule without installing

set -e

# Retrieve or update the hamlib source from GitHub
git submodule update --init --remote external/hamlib

cd external/hamlib
mkdir -p build
cd build
cmake ..
make -j$(nproc)
