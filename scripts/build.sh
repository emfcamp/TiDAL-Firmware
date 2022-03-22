#!/bin/bash
set -e -o pipefail

source /esp-idf/export.sh

cd /firmware
cd micropython
make -C mpy-cross

cd ports/esp32/boards
ln -sfn /firmware/YKW ./YKW

cd ..
make submodules BOARD=YKW USER_C_MODULES=/firmware/drivers/micropython.cmake
make BOARD=YKW USER_C_MODULES=/firmware/drivers/micropython.cmake $@
