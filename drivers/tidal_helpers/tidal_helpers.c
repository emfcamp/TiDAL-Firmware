#include "py/runtime.h"
#include "esp_log.h"
#include "sdkconfig.h"


STATIC mp_obj_t tidal_helper_get_variant() {
    mp_obj_t devboard = MP_ROM_QSTR(MP_QSTR_devboard);
    mp_obj_t proto = MP_ROM_QSTR(MP_QSTR_prototype);
    mp_obj_t prod = MP_ROM_QSTR(MP_QSTR_production);
    
    #ifdef CONFIG_TIDAL_VARIANT_DEVBOARD
        return devboard;
    #else
        #ifdef CONFIG_TIDAL_VARIANT_PROTOTYPE
            return proto;
        #else
            return prod;
        #endif
    #endif
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_helper_get_variant_obj, tidal_helper_get_variant);


STATIC const mp_rom_map_elem_t tidal_helpers_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ota) },
    { MP_ROM_QSTR(MP_QSTR_get_variant), MP_ROM_PTR(&tidal_helper_get_variant_obj) },
};
STATIC MP_DEFINE_CONST_DICT(tidal_helpers_module_globals, tidal_helpers_module_globals_table);

const mp_obj_module_t tidal_helpers_user_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&tidal_helpers_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_tidal_helpers, tidal_helpers_user_module, 1);
