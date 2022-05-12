# Create an INTERFACE library for our C module.
add_library(usermod_rtcmem INTERFACE)

# Add our source files to the lib
target_sources(usermod_rtcmem INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/driver_rtcmem.c
)

target_include_directories(usermod_ota INTERFACE
     ${CMAKE_CURRENT_LIST_DIR}/include
)

# Link our INTERFACE library to the usermod target.
target_link_libraries(usermod INTERFACE usermod_rtcmem)
