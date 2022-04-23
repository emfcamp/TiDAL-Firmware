set(IDF_TARGET esp32s3)

git_describe("TIDAL_GIT_VERSION" "${MICROPY_PORT_DIR}/../../../")
message("TIDAL_GIT_VERSION=${TIDAL_GIT_VERSION}")
configure_file("${MICROPY_PORT_DIR}/boards/tildamk6/sdkconfig.project_ver.in" "${MICROPY_PORT_DIR}/build-tildamk6/sdkconfig.project_ver")

set(SDKCONFIG_DEFAULTS
    boards/sdkconfig.base
    boards/sdkconfig.usb
    boards/sdkconfig.240mhz
    #boards/sdkconfig.spiram_sx
    #boards/tildamk6/sdkconfig.spiram.board
    boards/tildamk6/sdkconfig.board
    build-tildamk6/sdkconfig.project_ver
)

if(NOT MICROPY_FROZEN_MANIFEST)
    set(MICROPY_FROZEN_MANIFEST ${MICROPY_PORT_DIR}/boards/tildamk6/manifest.py)
endif()
