#!/bin/bash
# Build and install the wx-helios-direwolf submodule

set -e

# Initialize submodule if needed
if [ ! -d "external/direwolf" ] || [ ! -d "external/direwolf/.git" ]; then
    git submodule update --init external/direwolf
fi

cd external/direwolf
mkdir -p build
cd build
cmake ..
make -j$(nproc)
sudo make install

