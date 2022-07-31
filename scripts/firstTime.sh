#!/bin/bash

set -e
pushd esp-iot-solution
git reset --hard
git apply ../esp-iot-solution.diff
popd
pushd micropython
git reset --hard
git apply ../micropython.diff

# Backport framebuf enhancement from upstream micropython, see: https://github.com/micropython/micropython/issues/8987
git apply ../micropython-framebuf-enhancements.patch
popd
