
# Add the ESP IOT add-on
include(${CMAKE_CURRENT_LIST_DIR}/../esp-iot-solution/component.cmake)


# This top-level micropython.cmake is responsible for listing
# the individual modules we want to include.
# Paths are absolute, and ${CMAKE_CURRENT_LIST_DIR} can be
# used to prefix subdirectories.

# Add the HID interface
include(${CMAKE_CURRENT_LIST_DIR}/tilda_hid/micropython.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/../st7789/st7789/micropython.cmake)


