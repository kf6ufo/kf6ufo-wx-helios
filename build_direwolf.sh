#!/bin/bash
# Build the wx-helios-direwolf submodule without installing

set -e

# Retrieve or update the Direwolf source from GitHub
git submodule update --init --remote external/direwolf

cd external/direwolf
mkdir -p build
cd build
cmake ..
make -j$(nproc)

