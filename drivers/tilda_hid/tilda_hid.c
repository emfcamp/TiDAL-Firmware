// Include MicroPython API.
#include "py/runtime.h"
#include "soc/rtc.h"
#include "soc/rtc_cntl_reg.h"
#include "tinyusb.h"
#include "tusb_hid.h"
#include "esp_log.h"
#include "descriptors_control.h"
#include "tusb_console.h"
#include "tusb_cdc_acm.h"
#include "tinyusb.h"
#include "sdkconfig.h"


// Prevent the HID driver automatically reporting no buttons pressed after each
// report, so buttons are considered held until they're explicitly released
void tud_hid_report_complete_cb(uint8_t itf, uint8_t const *report, uint8_t len)
{
    // no-op
}


void tinyusb_hid_gamepad_report(int8_t x, int8_t y, int8_t z, int8_t rz, int8_t rx, int8_t ry, uint8_t hat, uint32_t buttons)
{
    // Remote wakeup
    if (tud_suspended()) {
        // Wake up host if we are in suspend mode
        // and REMOTE_WAKEUP feature is enabled by host
        tud_remote_wakeup();
    } else {
        // Send the 1st of report chain, the rest will be sent by tud_hid_report_complete_cb()
        // skip if hid is not ready yet
        if (!tud_hid_ready()) {
            return;
        }

        tud_hid_n_gamepad_report(0, 4, x, y, z, rz, rx, ry, hat, buttons);
    }
}




// This is the function which will be called from Python as tilda_hid.send_key(key).
STATIC mp_obj_t example_send_key(size_t n_args, const mp_obj_t *args) {
    // Extract the ints from the micropython input objects.
    uint8_t key[6] = { 0 };
    
    for (uint8_t i=0; i<n_args; i++) {
        key[i] = mp_obj_get_int_truncated(args[i]);
    }

    tinyusb_hid_keyboard_report(key);

    // Calculate the addition and convert to MicroPython object.
    return mp_const_none;
}
// Define a Python reference to the function above.
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(example_send_key_obj, 0, 6, example_send_key);


// This is the function which will be called from Python as tilda_hid.move_mouse(x, y).
STATIC mp_obj_t example_move_mouse(mp_obj_t a_obj, mp_obj_t b_obj) {
    // Extract the ints from the micropython input objects.
    int a = mp_obj_get_int(a_obj);
    int b = mp_obj_get_int(b_obj);
    
    
    tinyusb_hid_mouse_move_report(a, b, 0, 0);

    // Calculate the addition and convert to MicroPython object.
    return mp_const_none;
}
// Define a Python reference to the function above.
STATIC MP_DEFINE_CONST_FUN_OBJ_2(example_move_mouse_obj, example_move_mouse);

STATIC mp_obj_t example_set_usb_mode() {
    
    
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
    
    
    tinyusb_config_cdcacm_t amc_cfg = {
        .usb_dev = TINYUSB_USBDEV_0,
        .cdc_port = TINYUSB_CDC_ACM_0,
        .rx_unread_buf_sz = 64,
        .callback_rx = NULL,
        .callback_rx_wanted_char = NULL,
        .callback_line_state_changed = NULL,
        .callback_line_coding_changed = NULL
    };
    tusb_cdc_acm_init(&amc_cfg);    
    esp_tusb_init_console(TINYUSB_CDC_ACM_0);

    return mp_const_none; 
}

STATIC MP_DEFINE_CONST_FUN_OBJ_0(example_set_usb_mode_obj, example_set_usb_mode);


// Define all properties of the module.
// Table entries are key/value pairs of the attribute name (a string)
// and the MicroPython object reference.
// All identifiers and strings are written as MP_QSTR_xxx and will be
// optimized to word-sized integers by the build system (interned strings).
STATIC const mp_rom_map_elem_t example_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_tilda_hid) },
    { MP_ROM_QSTR(MP_QSTR_send_key), MP_ROM_PTR(&example_send_key_obj) },
    { MP_ROM_QSTR(MP_QSTR_move_mouse), MP_ROM_PTR(&example_move_mouse_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_usb_mode), MP_ROM_PTR(&example_set_usb_mode_obj) },
};
STATIC MP_DEFINE_CONST_DICT(example_module_globals, example_module_globals_table);

// Define module object.
const mp_obj_module_t example_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&example_module_globals,
};

// Register the module to make it available in Python.
// Note: the "1" in the third argument means this module is always enabled.
// This "1" can be optionally replaced with a macro like MODULE_CEXAMPLE_ENABLED
// which can then be used to conditionally enable this module.
MP_REGISTER_MODULE(MP_QSTR_tilda_hid, example_user_cmodule, 1);
