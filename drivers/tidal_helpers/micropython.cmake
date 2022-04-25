# Create an INTERFACE library for our C module.
add_library(usermod_tidal_helpers INTERFACE)

if(DEFINED ENV{CONFIG_TIDAL_VARIANT_DEVBOARD})
    target_compile_definitions(usermod_tidal_helpers INTERFACE CONFIG_TIDAL_VARIANT_DEVBOARD)
    message("Using devboard pins")
elseif (DEFINED ENV{CONFIG_TIDAL_VARIANT_PROTOTYPE})
    target_compile_definitions(usermod_tidal_helpers INTERFACE CONFIG_TIDAL_VARIANT_PROTOTYPE)
    message("Using prototype pins")
else()
    target_compile_definitions(usermod_tidal_helpers INTERFACE CONFIG_TIDAL_VARIANT_PRODUCTION)
    message("Using production pins")
endif()

# Add our source files to the lib
target_sources(usermod_tidal_helpers INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/tidal_helpers.c
)

# Link our INTERFACE library to the usermod target.
target_link_libraries(usermod INTERFACE usermod_tidal_helpers)
