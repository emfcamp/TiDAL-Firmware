# Create an INTERFACE library for our C module.
add_library(usermod_ecc108a INTERFACE)

# Add our source files to the lib
target_sources(usermod_ecc108a INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/ecc108a.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/atca_basic.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/atca_cfgs.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/atca_debug.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/atca_device.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/atca_helpers.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/atca_iface.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/atca_utils_sizes.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/cryptoauthlib.h
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_hmac.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_lock.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_secureboot.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_mac.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_nonce.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_updateextra.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_write.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_read.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_aes_gcm.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_ecdh.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_gendig.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_derivekey.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_genkey.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_execution.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_verify.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_sign.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_helpers.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_counter.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_selftest.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_basic.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_random.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_command.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_sha.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_privwrite.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_kdf.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_aes.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_checkmac.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib/calib_info.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/hal/atca_hal.c
#    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/hal/hal_esp32_i2c.c
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/hal/hal_esp32_mp_softi2c.c
)

target_include_directories(usermod_tidal_usb INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/calib
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/hal
    ${CMAKE_CURRENT_LIST_DIR}/cryptoauthlib/host
)

# Link our INTERFACE library to the usermod target.
target_link_libraries(usermod INTERFACE usermod_ecc108a)

