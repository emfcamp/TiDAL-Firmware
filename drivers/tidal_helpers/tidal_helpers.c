#include "py/runtime.h"
#include "esp_log.h"
#include "sdkconfig.h"
#include "mphalport.h"
#include "esp_sleep.h"


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

STATIC mp_obj_t tidal_esp_sleep_enable_gpio_wakeup() {
    esp_sleep_enable_gpio_wakeup();
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_esp_sleep_enable_gpio_wakeup_obj, tidal_esp_sleep_enable_gpio_wakeup);

STATIC mp_obj_t tidal_esp_sleep_pd_config(mp_obj_t domain_obj, mp_obj_t option_obj) {
    esp_sleep_pd_domain_t domain = (esp_sleep_pd_domain_t)mp_obj_get_int(domain_obj);
    esp_sleep_pd_option_t option = (esp_sleep_pd_option_t)mp_obj_get_int(option_obj);
    esp_err_t err = esp_sleep_pd_config(domain, option);
    check_esp_err(err);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(tidal_esp_sleep_pd_config_obj, tidal_esp_sleep_pd_config);

STATIC mp_obj_t tidal_gpio_wakeup(mp_obj_t gpio_obj, mp_obj_t level_obj) {
    gpio_num_t gpio = (gpio_num_t)mp_obj_get_int(gpio_obj);
    gpio_int_type_t level = (gpio_int_type_t)mp_obj_get_int(level_obj);
    esp_err_t err;
    if (level) {
        err = gpio_wakeup_enable(gpio, level);
    } else {
        err = gpio_wakeup_disable(gpio);
    }
    check_esp_err(err);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(tidal_gpio_wakeup_obj, tidal_gpio_wakeup);

STATIC mp_obj_t tidal_gpio_hold(mp_obj_t gpio_obj, mp_obj_t flag_obj) {
    gpio_num_t gpio = (gpio_num_t)mp_obj_get_int(gpio_obj);
    int flag = (gpio_int_type_t)mp_obj_is_true(flag_obj);
    esp_err_t err;
    if (flag) {
        err = gpio_hold_en(gpio);
    } else {
        err = gpio_hold_dis(gpio);
    }
    check_esp_err(err);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(tidal_gpio_hold_obj, tidal_gpio_hold);

STATIC mp_obj_t tidal_gpio_sleep_sel(mp_obj_t gpio_obj, mp_obj_t flag_obj) {
    gpio_num_t gpio = (gpio_num_t)mp_obj_get_int(gpio_obj);
    bool flag = mp_obj_is_true(flag_obj);
    esp_err_t err;
    if (flag) {
        err = gpio_sleep_sel_en(gpio);
    } else {
        err = gpio_sleep_sel_dis(gpio);
    }
    check_esp_err(err);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(tidal_gpio_sleep_sel_obj, tidal_gpio_sleep_sel);

STATIC mp_obj_t tidal_esp_sleep_enable_gpio_switch(mp_obj_t flag_obj) {
    bool flag = mp_obj_is_true(flag_obj);
    esp_sleep_enable_gpio_switch(flag);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_esp_sleep_enable_gpio_switch_obj, tidal_esp_sleep_enable_gpio_switch);


STATIC const mp_rom_map_elem_t tidal_helpers_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ota) },
    { MP_ROM_QSTR(MP_QSTR_get_variant), MP_ROM_PTR(&tidal_helper_get_variant_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_sleep_enable_gpio_wakeup), MP_ROM_PTR(&tidal_esp_sleep_enable_gpio_wakeup_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_sleep_pd_config), MP_ROM_PTR(&tidal_esp_sleep_pd_config_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_wakeup), MP_ROM_PTR(&tidal_gpio_wakeup_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_hold), MP_ROM_PTR(&tidal_gpio_hold_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_sleep_sel), MP_ROM_PTR(&tidal_gpio_sleep_sel_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_sleep_enable_gpio_switch), MP_ROM_PTR(&tidal_esp_sleep_enable_gpio_switch_obj) },

    { MP_ROM_QSTR(MP_QSTR_ESP_PD_DOMAIN_RTC_PERIPH), MP_ROM_INT(ESP_PD_DOMAIN_RTC_PERIPH) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_OPTION_OFF), MP_ROM_INT(ESP_PD_OPTION_OFF) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_OPTION_ON), MP_ROM_INT(ESP_PD_OPTION_ON) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_OPTION_AUTO), MP_ROM_INT(ESP_PD_OPTION_AUTO) },
};
STATIC MP_DEFINE_CONST_DICT(tidal_helpers_module_globals, tidal_helpers_module_globals_table);

const mp_obj_module_t tidal_helpers_user_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&tidal_helpers_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_tidal_helpers, tidal_helpers_user_module, 1);
