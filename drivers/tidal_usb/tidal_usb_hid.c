#include "py/runtime.h"
#include "esp_log.h"
#include "tinyusb.h"
#include "tusb_hid.h"
#include "usb.h"
#include "tidal_usb_hid.h"
#include "descriptors_control.h"
#if CFG_TUD_U2FHID
#include "tidal_usb_u2f.h"
#endif

static const char *TAG = "tidalHID";

void tud_hid_set_report_cb(uint8_t itf, uint8_t report_id, hid_report_type_t report_type, uint8_t const* buffer, uint16_t bufsize) { 
    printf("REPORT: %d %d %d\n", itf, report_id, report_type);
    #if CFG_TUD_U2FHID
    if (itf == 0+(CFG_TUD_HID_KBD)) {
        // This is the U2F device
        handle_report_u2f(itf, report_id, report_type, buffer, bufsize);
    }
    #endif
}

// Prevent the HID driver automatically reporting no buttons pressed after each
// report, so buttons are considered held until they're explicitly released
void tud_hid_report_complete_cb(uint8_t itf, uint8_t const *report, uint8_t len)
{
    ESP_LOGW(TAG, "HID report complete");
    #if CFG_TUD_U2FHID
        // Also send any pending U2F reports
        pop_and_send_report();
    #endif
}

// Send up to 6 keyboard scancodes
STATIC mp_obj_t tidal_hid_send_key(size_t n_args, const mp_obj_t *args) {
    // The default report if no keys are provided is all NULL (no key pressed)
    uint8_t key[6] = { 0 };

    // Extract the ints from the micropython input objects.
    // The number of args is limited by the function definition
    for (uint8_t i=0; i<n_args; i++) {
        key[i] = mp_obj_get_int_truncated(args[i]);
    }

    // Send the USB report
    tinyusb_hid_keyboard_report(key);

    // Return None
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(tidal_hid_send_key_obj, 0, 6, tidal_hid_send_key);


// Send a mouse move report
STATIC mp_obj_t tidal_hid_move_mouse(mp_obj_t a_obj, mp_obj_t b_obj) {
    // Extract the ints from the micropython input objects.
    int a = mp_obj_get_int(a_obj);
    int b = mp_obj_get_int(b_obj);

    // Send the USB report
    tinyusb_hid_mouse_move_report(a, b, 0, 0);

    // Return None
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(tidal_hid_move_mouse_obj, tidal_hid_move_mouse);

// --------------------------------------------------------------------------- //

// Define the module globals table
STATIC const mp_rom_map_elem_t tidal_hid_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_tilda_hid) },
    { MP_ROM_QSTR(MP_QSTR_send_key), MP_ROM_PTR(&tidal_hid_send_key_obj) },
    { MP_ROM_QSTR(MP_QSTR_move_mouse), MP_ROM_PTR(&tidal_hid_move_mouse_obj) },
};
STATIC MP_DEFINE_CONST_DICT(tidal_hid_module_globals, tidal_hid_module_globals_table);

// Define module object but don't register it at the top level
const mp_obj_module_t tidal_hid_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&tidal_hid_module_globals,
};
