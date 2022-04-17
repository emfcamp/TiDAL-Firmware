
# Add the ESP IOT add-on
include(${CMAKE_CURRENT_LIST_DIR}/../esp-iot-solution/component.cmake)


# Add the HID interface
include(${CMAKE_CURRENT_LIST_DIR}/tidal_usb/micropython.cmake)

# Add the st7789 driver
include(${CMAKE_CURRENT_LIST_DIR}/../st7789/st7789/micropython.cmake)


