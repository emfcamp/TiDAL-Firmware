#include "py/runtime.h"
#include "atca_iface.h"
#include "atca_basic.h"
#include "py/objstr.h"
#include <endian.h>


bool inited = false;
ATCAIfaceCfg cfg_atecc108a_i2c_default = {
    .iface_type                 = ATCA_I2C_IFACE,
    .devtype                    = ATECC108A,
    {
        .atcai2c.address        = 0x60,
        .atcai2c.bus            = 0,
        /* This is overridden in hal/hal_esp32_i2c.c but also read elsewhere */
        .atcai2c.baud           = 100000,
    },
    .wake_delay                 = 1500,
    .rx_retries                 = 2
};


void assert_ATCA_SUCCESS(ATCA_STATUS status) {
    if (status != ATCA_SUCCESS) {
        mp_raise_OSError(status);
    }
}


STATIC mp_obj_t ecc108a_init() {
    assert_ATCA_SUCCESS(atcab_init(&cfg_atecc108a_i2c_default));
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(ecc108a_init_obj, ecc108a_init);


STATIC mp_obj_t ecc108a_read_config() {
    assert_ATCA_SUCCESS(atcab_wakeup());
    uint8_t buf[128] = {0};
    assert_ATCA_SUCCESS(atcab_read_config_zone(&buf));
    return mp_obj_new_bytearray(sizeof(buf), buf);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(ecc108a_read_config_obj, ecc108a_read_config);


STATIC mp_obj_t ecc108a_get_serial_number() {
    uint8_t serial[9] = { 0 };
    char serial_str[27] = "";

    assert_ATCA_SUCCESS(atcab_wakeup());
    assert_ATCA_SUCCESS(atcab_read_serial_number(&serial));

    sprintf(&serial_str, "%02x:%02x:%02x:%02x:%02x:%02x:%02x:%02x:%02x",
        serial[0], serial[1], serial[2],
        serial[3], serial[4], serial[5],
        serial[6], serial[7], serial[8]
    );

    return mp_obj_new_str(serial_str, 26);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(ecc108a_get_serial_number_obj, ecc108a_get_serial_number);


STATIC mp_obj_t ecc108a_provision_slot() {
    // Retrieve the current configuration zone and patch it
    /*
    Desired state from ecc108a_tools.run()
    Key n:
      SlotLocked: 1 (unlocked)
      SlotConfig: 6083
      KeyConfig: 0033
      UseFlag: 0xff
    */
    uint8_t buf[128] = {0};
    assert_ATCA_SUCCESS(atcab_read_config_zone(&buf));

    uint16_t slot_config = 
        ATCA_SLOT_CONFIG_EXT_SIG_MASK |
        ATCA_SLOT_CONFIG_INT_SIG_MASK |
        ATCA_SLOT_CONFIG_IS_SECRET_MASK |
        ATCA_SLOT_CONFIG_WRITE_KEY(0) |
        ATCA_SLOT_CONFIG_WRITE_CONFIG(0b0110)
    ;
    uint16_t key_config = 
        ATCA_KEY_CONFIG_PRIVATE_MASK |
        ATCA_KEY_CONFIG_PUB_INFO_MASK |
        ATCA_KEY_CONFIG_KEY_TYPE(4) |
        ATCA_KEY_CONFIG_LOCKABLE_MASK
    ;
    
    // Patch this config into each of the 16 slots
    for (uint8_t i = 0; i < 16 ; i++) {
        uint16_t *target_slot_config = &buf[20 + 2*i];
        *target_slot_config = slot_config;
        
        uint16_t *target_key_config = &buf[96 + 2*i];
        *target_key_config = key_config;
    }

    assert_ATCA_SUCCESS(atcab_write_config_zone(&buf));
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(ecc108a_provision_slot_obj, ecc108a_provision_slot);


STATIC mp_obj_t ecc108a_lock_data_zone() {
    assert_ATCA_SUCCESS(atcab_lock_data_zone());
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(ecc108a_lock_data_zone_obj, ecc108a_lock_data_zone);


STATIC mp_obj_t ecc108a_lock_config_zone() {
    assert_ATCA_SUCCESS(atcab_lock_config_zone());
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(ecc108a_lock_config_zone_obj, ecc108a_lock_config_zone);


STATIC mp_obj_t ecc108a_lock_slot(mp_obj_t slot_id) {
    uint8_t slot = mp_obj_get_int(slot_id);
    assert_ATCA_SUCCESS(atcab_lock_data_slot(slot));
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ecc108a_lock_slot_obj, ecc108a_lock_slot);


STATIC mp_obj_t ecc108a_genkey(mp_obj_t slot_id) {
    uint8_t pubkey[64] = { 0 };
    uint8_t slot = mp_obj_get_int(slot_id);

    //assert_ATCA_SUCCESS(atcab_wakeup());
    assert_ATCA_SUCCESS(atcab_genkey(slot, &pubkey));

    // Return X, Y tuple
    mp_obj_t tuple[2];
    tuple[0] = mp_obj_new_bytes(pubkey, 32);
    tuple[1] = mp_obj_new_bytes(pubkey+32, 32);
    return mp_obj_new_tuple(2, tuple);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ecc108a_genkey_obj, ecc108a_genkey);


STATIC mp_obj_t ecc108a_get_pubkey(mp_obj_t slot_id) {
    uint8_t pubkey[64] = { 0 };
    uint8_t slot = mp_obj_get_int(slot_id);

    //assert_ATCA_SUCCESS(atcab_wakeup());
    assert_ATCA_SUCCESS(atcab_get_pubkey(slot, &pubkey));

    // Return X, Y tuple
    mp_obj_t tuple[2];
    tuple[0] = mp_obj_new_bytes(pubkey, 32);
    tuple[1] = mp_obj_new_bytes(pubkey+32, 32);
    return mp_obj_new_tuple(2, tuple);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ecc108a_get_pubkey_obj, ecc108a_get_pubkey);


STATIC mp_obj_t ecc108a_sign(mp_obj_t slot_id, mp_obj_t message) {
    uint8_t signature[64] = { 0 };
    uint8_t slot = mp_obj_get_int(slot_id);
    
    mp_check_self(mp_obj_is_str_or_bytes(message));
    GET_STR_DATA_LEN(message, msg, str_len);
    
    //assert_ATCA_SUCCESS(atcab_wakeup());
    assert_ATCA_SUCCESS(atcab_sign(slot, &msg, &signature));

    // Return R, S tuple
    mp_obj_t tuple[2];
    tuple[0] = mp_obj_new_bytes(signature, 32);
    tuple[1] = mp_obj_new_bytes(signature+32, 32);
    return mp_obj_new_tuple(2, tuple);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(ecc108a_sign_obj, ecc108a_sign);


STATIC mp_obj_t ecc108a_verify(mp_obj_t message, mp_obj_t signature, mp_obj_t public_key) {
    // All the strings are length 32, but we need to pass a *pointer* to a size t.
    const size_t thirtytwo = 32;
    
    // Extract the pubkey
    mp_obj_tuple_t *public_key_tuple = MP_OBJ_TO_PTR(public_key);
    const char *x = mp_obj_str_get_data(public_key_tuple->items[0], &thirtytwo);
    const char *y = mp_obj_str_get_data(public_key_tuple->items[1], &thirtytwo);
    uint8_t key[64];
    memcpy(&key[0], x, 32);
    memcpy(&key[32], y, 32);
    
    // Extract the signature
    mp_obj_tuple_t *signature_tuple = MP_OBJ_TO_PTR(signature);
    const char *r = mp_obj_str_get_data(signature_tuple->items[0], &thirtytwo);
    const char *s = mp_obj_str_get_data(signature_tuple->items[1], &thirtytwo);
    uint8_t sig[64];
    memcpy(&sig[0], r, 32);
    memcpy(&sig[32], s, 32);
    
    // Extract the message (this is a SHA256 of the user-facing 'message')
    const char *message_data = mp_obj_str_get_data(message, &thirtytwo);

    // Verify on-chip
    bool verified;
    assert_ATCA_SUCCESS(atcab_verify_extern((const uint8_t*) message_data, &sig, &key, &verified));
    if (verified)
        return mp_const_true;
    else
        return mp_const_false;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_3(ecc108a_verify_obj, ecc108a_verify);


STATIC const mp_rom_map_elem_t ecc108a_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ecc108a) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&ecc108a_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_read_config), MP_ROM_PTR(&ecc108a_read_config_obj) },
    { MP_ROM_QSTR(MP_QSTR_provision_slot), MP_ROM_PTR(&ecc108a_provision_slot_obj) },
    { MP_ROM_QSTR(MP_QSTR_lock_data_zone), MP_ROM_PTR(&ecc108a_lock_data_zone_obj) },
    { MP_ROM_QSTR(MP_QSTR_lock_config_zone), MP_ROM_PTR(&ecc108a_lock_config_zone_obj) },
    { MP_ROM_QSTR(MP_QSTR_lock_slot), MP_ROM_PTR(&ecc108a_lock_slot_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_serial_number), MP_ROM_PTR(&ecc108a_get_serial_number_obj) },
    { MP_ROM_QSTR(MP_QSTR_genkey), MP_ROM_PTR(&ecc108a_genkey_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_pubkey), MP_ROM_PTR(&ecc108a_get_pubkey_obj) },
    { MP_ROM_QSTR(MP_QSTR_sign), MP_ROM_PTR(&ecc108a_sign_obj) },
    { MP_ROM_QSTR(MP_QSTR_verify), MP_ROM_PTR(&ecc108a_verify_obj) },
};
STATIC MP_DEFINE_CONST_DICT(ecc108a_module_globals, ecc108a_module_globals_table);

const mp_obj_module_t ecc108a_user_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&ecc108a_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_ecc108a, ecc108a_user_module, 1);
