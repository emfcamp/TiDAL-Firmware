# Create an INTERFACE library for our C module.
add_library(usermod_lodepng INTERFACE)

#target_compile_definitions(usermod_lodepng INTERFACE ...)


# Add our source files to the lib
target_sources(usermod_lodepng INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/lodepng_wrapper.c
)

target_include_directories(usermod_lodepng INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/../../lodepng
)

# Link our INTERFACE library to the usermod target.
target_link_libraries(usermod INTERFACE usermod_lodepng)
