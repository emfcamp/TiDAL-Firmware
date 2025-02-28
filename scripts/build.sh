#!/bin/bash
set -e -o pipefail

source /esp-idf/export.sh
export IOT_SOLUTION_PATH=/firmware/esp-iot-solution

cd /firmware
cd micropython
make -C mpy-cross

cd ports/esp32/boards
ln -sfn /firmware/tildamk6 ./tildamk6

cd ..
make submodules BOARD=tildamk6 USER_COMPONENTS=/firmware/components/tinyusb USER_C_MODULES=/firmware/drivers/micropython.cmake
make BOARD=tildamk6 USER_COMPONENTS=/firmware/components/tinyusb USER_C_MODULES=/firmware/drivers/micropython.cmake $@
