#!/bin/bash

set -e
pushd esp-iot-solution
git reset --hard
git apply ../esp-iot-solution.diff
popd
pushd micropython
git reset --hard
git apply ../micropython.diff
popd
