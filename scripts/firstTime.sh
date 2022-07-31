#!/bin/bash

set -e
pushd esp-iot-solution
git reset --hard
git apply ../esp-iot-solution.diff
popd
pushd micropython
git reset --hard
git apply ../micropython.diff

# Backport fix from upstream micropython, see: https://github.com/micropython/micropython/issues/8436
git apply ../micropython-dynamic-natmod-build-fix.patch
popd
