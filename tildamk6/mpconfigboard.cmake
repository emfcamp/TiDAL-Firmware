set(IDF_TARGET esp32s3)

# Override the --dirty set by git_describe, because our build process always dirties submodules so it's not worth remarking on
git_describe("TIDAL_GIT_VERSION" "${MICROPY_PORT_DIR}/../../../" --dirty=)
message("TIDAL_GIT_VERSION=${TIDAL_GIT_VERSION}")
configure_file("${MICROPY_PORT_DIR}/boards/tildamk6/sdkconfig.project_ver.in" "${MICROPY_PORT_DIR}/build-tildamk6/sdkconfig.project_ver")
if(DEFINED ENV{CONFIG_TIDAL_VARIANT_DEVBOARD})
    set(SDKCONFIG_DEFAULTS
        boards/sdkconfig.base
        boards/sdkconfig.usb
        boards/sdkconfig.240mhz
        #boards/sdkconfig.spiram_sx
        #boards/tildamk6/sdkconfig.spiram.board
        boards/tildamk6/sdkconfig.board
        build-tildamk6/sdkconfig.project_ver
    )
elseif (DEFINED ENV{CONFIG_TIDAL_VARIANT_PROTOTYPE})
    set(SDKCONFIG_DEFAULTS
        boards/sdkconfig.base
        boards/sdkconfig.usb
        boards/sdkconfig.240mhz
        #boards/sdkconfig.spiram_sx
        #boards/tildamk6/sdkconfig.spiram.board
        boards/tildamk6/sdkconfig.board
        build-tildamk6/sdkconfig.project_ver
    )
else()
    set(SDKCONFIG_DEFAULTS
        boards/sdkconfig.base
        boards/sdkconfig.usb
        boards/sdkconfig.240mhz
        boards/sdkconfig.spiram_sx
        boards/tildamk6/sdkconfig.spiram.board
        boards/tildamk6/sdkconfig.board
        build-tildamk6/sdkconfig.project_ver
    )
endif()

if(NOT MICROPY_FROZEN_MANIFEST)
    set(MICROPY_FROZEN_MANIFEST ${MICROPY_PORT_DIR}/boards/tildamk6/manifest.py)
endif()
