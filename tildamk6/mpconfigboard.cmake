set(IDF_TARGET esp32s3)

set(SDKCONFIG_DEFAULTS
    boards/sdkconfig.base
    boards/sdkconfig.usb
    boards/sdkconfig.240mhz
    #boards/sdkconfig.spiram_sx
    #boards/tildamk6/sdkconfig.spiram.board
    boards/tildamk6/sdkconfig.board
)

if(NOT MICROPY_FROZEN_MANIFEST)
    set(MICROPY_FROZEN_MANIFEST ${MICROPY_PORT_DIR}/boards/tildamk6/manifest.py)
endif()
