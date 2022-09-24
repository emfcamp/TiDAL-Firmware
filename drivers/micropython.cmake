
# Add the ESP IOT add-on
include(${CMAKE_CURRENT_LIST_DIR}/../esp-iot-solution/component.cmake)


# Add the HID interface
include(${CMAKE_CURRENT_LIST_DIR}/tidal_usb/micropython.cmake)

# Add the st7789 driver
include(${CMAKE_CURRENT_LIST_DIR}/../st7789/st7789/micropython.cmake)


list(APPEND EXTRA_COMPONENT_DIRS
    "$ENV{IDF_PATH}/components/esp_http_client"
    "$ENV{IDF_PATH}/components/esp_https_ota"
)

# Add the OTA driver
include(${CMAKE_CURRENT_LIST_DIR}/ota/micropython.cmake)

# Add general purpose helpers
include(${CMAKE_CURRENT_LIST_DIR}/tidal_helpers/micropython.cmake)

include(${CMAKE_CURRENT_LIST_DIR}/lodepng/micropython.cmake)

include(${CMAKE_CURRENT_LIST_DIR}/../tidal3d/module/micropython.cmake)
