#include "py/runtime.h"
#include "py/objstr.h"
#include "py/objtuple.h"
#include "esp_log.h"
#include "sdkconfig.h"
#include "mphalport.h"
#include "modmachine.h" // for machine_pin_type
#include "esp_sleep.h"
#include "esp_wifi.h"
#include "device/usbd.h"
#include "rom/uart.h"
#include "soc/rtc_cntl_reg.h"
#include "esp32s2/rom/usb/usb_dc.h"
#include "esp32s2/rom/usb/chip_usb_dw_wrapper.h"
#include "esp32s2/rom/usb/usb_persist.h"
#include "esp_wpa2.h"
#include "driver/ledc.h"
#include "tidal_usb_u2f_shared_variables.h"


STATIC mp_obj_t tidal_authentication_authentication_operation() {
    return mp_obj_new_int(authentication_operation);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_authentication_authentication_operation_obj, tidal_authentication_authentication_operation);

STATIC mp_obj_t tidal_authentication_authentication_requested() {
    mp_obj_t response[3];
    response[0] = mp_const_none;
    response[1] = mp_const_none;
    response[2] = mp_const_none;
    
    // Is the current operation a request?
    if (authentication_operation == AUTHENTICATE_REQUEST || authentication_operation == REGISTER_REQUEST) {
        response[0] = mp_const_true;
    } else {
        response[0] = mp_const_false;
    }
    // What slot is in use
    if (authentication_operation_slot == 99) {
            response[1] = mp_const_none;
    } else {
        response[1] = mp_obj_new_int(authentication_operation_slot);
    }
    // What's the application parameter
    response[2] = mp_obj_new_bytes(authentication_application_parameter, 32);
    return mp_obj_new_tuple(3, response);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_authentication_authentication_requested_obj, tidal_authentication_authentication_requested);

STATIC mp_obj_t tidal_authentication_authentication_mismatch() {
    authentication_operation = KEY_MISMATCH;
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_authentication_authentication_mismatch_obj, tidal_authentication_authentication_mismatch);

STATIC mp_obj_t tidal_authentication_authentication_approve(mp_obj_t state) {
    if (state == mp_const_true) {
        if (authentication_operation == AUTHENTICATE_REQUEST)
            authentication_operation = AUTHENTICATE_APPROVED;
        if (authentication_operation == REGISTER_REQUEST)
            authentication_operation = REGISTER_APPROVED;
    }
    if (state == mp_const_false)
        authentication_operation = USER_REFUSED;
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_authentication_authentication_approve_obj, tidal_authentication_authentication_approve);


STATIC mp_obj_t tidal_authentication_authentication_slot(mp_obj_t slot) {
    if (mp_obj_is_int(slot)) {
        authentication_operation_slot = mp_obj_get_int(slot);
        return slot;
    } else {
        mp_raise_ValueError(slot);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_authentication_authentication_slot_obj, tidal_authentication_authentication_slot);


STATIC mp_obj_t tidal_authentication_to_sign() {
    mp_obj_t response;
    response = mp_obj_new_bytearray_by_ref(authentication_length_to_sign, authentication_value_to_sign);
    return response;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_authentication_to_sign_obj, tidal_authentication_to_sign);




STATIC mp_obj_t tidal_authentication_last_signature() {
    mp_obj_t response;
    response = mp_obj_new_bytearray_by_ref(64, authentication_signature);
    return response;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_authentication_last_signature_obj, tidal_authentication_last_signature);



STATIC mp_obj_t tidal_authentication_set_signature(mp_obj_t signature_in) {
    mp_obj_t *tuple_data = NULL;
    size_t tuple_len;
    memset(&authentication_signature, 0x00, 64);
    
    mp_obj_tuple_get(signature_in, &tuple_len, &tuple_data);
    if (tuple_len == 2) {
        for (size_t i=0; i<2; i++) {
            if (mp_obj_is_str_or_bytes(tuple_data[i])) {
                GET_STR_DATA_LEN(tuple_data[i], sig, sig_len);
                if (sig_len == 32) {
                    memcpy((char *)authentication_signature + (i*32), (char *) sig, 32);
                } else {
                    return mp_const_false;
                }
            } else {
                return mp_const_false;
            }
        }
    } else {
        return mp_const_false;
    }
    return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_authentication_set_signature_obj, tidal_authentication_set_signature);


STATIC mp_obj_t tidal_authentication_set_pubkey(mp_obj_t pubkey_in) {
    mp_obj_t *tuple_data = NULL;
    size_t tuple_len;
    
    mp_obj_tuple_get(pubkey_in, &tuple_len, &tuple_data);
    if (tuple_len == 2) {
        for (size_t i=0; i<2; i++) {
            if (mp_obj_is_str_or_bytes(tuple_data[i])) {
                GET_STR_DATA_LEN(tuple_data[i], pk, pk_len);
                if (pk_len == 32) {
                    memcpy((char *)authentication_pubkey + (i*32), (char *) pk, 32);
                } else {
                    return mp_const_false;
                }
            } else {
                return mp_const_false;
            }
        }
    } else {
        return mp_const_false;
    }
    return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_authentication_set_pubkey_obj, tidal_authentication_set_pubkey);



STATIC const mp_rom_map_elem_t tidal_authentication_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_tidal_authentication) },
    { MP_ROM_QSTR(MP_QSTR_get_authentication_operation), MP_ROM_PTR(&tidal_authentication_authentication_operation_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_authentication_approval), MP_ROM_PTR(&tidal_authentication_authentication_approve_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_authentication_requested), MP_ROM_PTR(&tidal_authentication_authentication_requested_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_authentication_mismatch), MP_ROM_PTR(&tidal_authentication_authentication_mismatch_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_authentication_slot), MP_ROM_PTR(&tidal_authentication_authentication_slot_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_to_sign), MP_ROM_PTR(&tidal_authentication_to_sign_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_signature), MP_ROM_PTR(&tidal_authentication_set_signature_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_pubkey), MP_ROM_PTR(&tidal_authentication_set_pubkey_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_last_signature), MP_ROM_PTR(&tidal_authentication_last_signature_obj) },
    

};
STATIC MP_DEFINE_CONST_DICT(tidal_authentication_module_globals, tidal_authentication_module_globals_table);

const mp_obj_module_t tidal_authentication_user_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&tidal_authentication_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_tidal_authentication, tidal_authentication_user_module, 1);
