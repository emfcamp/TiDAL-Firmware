#include "py/runtime.h"
#include "atca_iface.h"
#include "atca_basic.h"


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

STATIC mp_obj_t ecc108a_read_config() {

    int status = atcab_init(&cfg_atecc108a_i2c_default);
    if (status < 0) {
        mp_raise_OSError(status);
    }
    status = atcab_wakeup();
    if (status < 0) {
        mp_raise_OSError(status);
    }

    uint8_t buf[128] = {0};
    for (int i = 0; i < sizeof(buf); i += 32) {
        status = atcab_read_zone(ATCA_ZONE_CONFIG, 0, 0, i, &buf[i], 32);
    }
    return mp_obj_new_bytearray_by_ref(sizeof(buf), buf);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(ecc108a_read_config_obj, ecc108a_read_config);


STATIC const mp_rom_map_elem_t ecc108a_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ecc108a) },
    { MP_ROM_QSTR(MP_QSTR_read_config), MP_ROM_PTR(&ecc108a_read_config_obj) },
};
STATIC MP_DEFINE_CONST_DICT(ecc108a_module_globals, ecc108a_module_globals_table);

const mp_obj_module_t ecc108a_user_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&ecc108a_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_ecc108a, ecc108a_user_module, 1);
