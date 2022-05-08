# Create an INTERFACE library for our C module.
add_library(usermod_tidal_usb INTERFACE)

# Add our source files to the lib
target_sources(usermod_tidal_usb INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/tidal_usb.c
    ${CMAKE_CURRENT_LIST_DIR}/tidal_usb_hid.c
    ${CMAKE_CURRENT_LIST_DIR}/tidal_usb_console.c
    ${CMAKE_CURRENT_LIST_DIR}/tidal_usb_u2f.c
)

# Add the current directory as an include directory.
target_include_directories(usermod_tidal_usb INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

# Link our INTERFACE library to the usermod target.
target_link_libraries(usermod INTERFACE usermod_tidal_usb)
