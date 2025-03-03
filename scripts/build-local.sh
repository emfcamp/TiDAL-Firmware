#!/bin/bash
# This build script is used to build the project outside of the docker container.
# This has been tested on a native Ubuntu 20.04 LTS only, I am not sure if it will work on other platforms.
# It should be executed from the project root directory.

set -e -o pipefail

# Get the current directory and assign to a variable
export ROOTDIR=`pwd`

source ./esp-idf/export.sh
export IOT_SOLUTION_PATH=$ROOTDIR/esp-iot-solution
export TARGET=esp32s3
export CONFIG_TIDAL_VARIANT_DEVBOARD=y

cd $ROOTDIR/micropython
make -C mpy-cross

cd $ROOTDIR/micropython/ports/esp32/boards

ln -sfn $ROOTDIR/tildamk6 $ROOTDIR/micropython/ports/esp32/boards/tildamk6

cd $ROOTDIR/micropython/ports/esp32

# Make sure we update the manifest, otherwise changes will not be picked up
rm build-tildamk6/frozen_content.c || true

make submodules BOARD=tildamk6 USER_C_MODULES="$ROOTDIR"/drivers/micropython.cmake CONFIG_TIDAL_VARIANT_DEVBOARD=y
make BOARD=tildamk6 USER_C_MODULES="$ROOTDIR"/drivers/micropython.cmake CONFIG_TIDAL_VARIANT_DEVBOARD=y $@
