#include "py/runtime.h"
#include "tinyusb.h"
#include "tidal_usb_console.h"
#include "tidal_usb_hid.h"


// USB init function
STATIC mp_obj_t tidal_usb_initialize() {
    // Set RTC peripheral register bits:
    // RTC_CNTL_SW_HW_USB_PHY_SEL - allow runtime USB PHY attachment mode selection
    // RTC_CNTL_SW_USB_PHY_SEL - attach USB-OTG to internal PHY
    SET_PERI_REG_MASK(RTC_CNTL_USB_CONF_REG,
                      RTC_CNTL_SW_HW_USB_PHY_SEL | RTC_CNTL_SW_USB_PHY_SEL);

    
    /* Install tinyusb driver, Please enable `CONFIG_TINYUSB_HID_ENABLED` in menuconfig */
    tinyusb_config_t tusb_cfg = {
        .descriptor = NULL,
        .string_descriptor = NULL,
        .external_phy = false // In the most cases you need to use a `false` value
    };
    tinyusb_driver_install(&tusb_cfg);
    tidal_configure_usb_console();
    return mp_const_none; 
}

STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_usb_initialize_obj, tidal_usb_initialize);

// --------------------------------------------------------------------------- //

// Definition of the contents of the module
STATIC const mp_rom_map_elem_t tidal_usb_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR__tidal_usb) },
    { MP_ROM_QSTR(MP_QSTR_hid), MP_ROM_PTR(&tidal_hid_module) },
    { MP_ROM_QSTR(MP_QSTR_console), MP_ROM_PTR(&tidal_console_module) },
    { MP_ROM_QSTR(MP_QSTR_initialize), MP_ROM_PTR(&tidal_usb_initialize_obj) },
};
STATIC MP_DEFINE_CONST_DICT(tidal_usb_module_globals, tidal_usb_module_globals_table);

// module object
const mp_obj_module_t tidal_usb_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&tidal_usb_module_globals,
};

// Regisiter as a top-level module
MP_REGISTER_MODULE(MP_QSTR__tidal_usb, tidal_usb_module, 1);