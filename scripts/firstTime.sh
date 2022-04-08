#!/bin/bash

pushd esp-iot-solution
git apply ../esp-iot-solution.diff
popd
pushd micropython
git apply ../micropython.diff
popd