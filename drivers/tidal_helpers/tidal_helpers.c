#include "py/runtime.h"
#include "esp_log.h"
#include "sdkconfig.h"
#include "mphalport.h"
#include "modmachine.h" // for machine_pin_type
#include "esp_sleep.h"
#include "rom/uart.h"

// Have to redefine this from machine_pin.c, unfortunately
typedef struct _machine_pin_obj_t {
    mp_obj_base_t base;
    gpio_num_t id;
} machine_pin_obj_t;

STATIC gpio_num_t get_pin(mp_obj_t pin_obj) {
    if (mp_obj_is_int(pin_obj)) {
        return (gpio_num_t)mp_obj_get_int(pin_obj);
    } else if (mp_obj_get_type(pin_obj) != &machine_pin_type) {
        mp_raise_ValueError(MP_ERROR_TEXT("expecting a pin or integer pin number"));
    }
    machine_pin_obj_t *self = pin_obj;
    return self->id;
}

STATIC mp_obj_t tidal_helper_get_variant() {
    mp_obj_t devboard = MP_ROM_QSTR(MP_QSTR_devboard);
    mp_obj_t proto = MP_ROM_QSTR(MP_QSTR_prototype);
    mp_obj_t prod = MP_ROM_QSTR(MP_QSTR_production);
    #if defined(CONFIG_TIDAL_VARIANT_DEVBOARD)
        (void)proto; (void)prod;
        return devboard;
    #elif defined(CONFIG_TIDAL_VARIANT_PROTOTYPE)
        (void)devboard; (void)prod;
        return proto;
    #else
        (void)devboard; (void)proto;
        return prod;
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
    gpio_num_t gpio = get_pin(gpio_obj);
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
    gpio_num_t gpio = get_pin(gpio_obj);
    bool flag = mp_obj_is_true(flag_obj);
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

STATIC void tidal_lightsleep_isr(void *arg) {
    gpio_num_t gpio = (gpio_num_t)arg;
    // Lightsleep GPIO interrupts are always level triggered, meaning we need to
    // immediately disable it to prevent it firing continuously (which will
    // almost immediately cause the IRQ watchdog to expire and reset the board).
    // It is the responsibility of the handler to re-enable or reconfigure it as
    // needed. Note that this alone doesn't prevent the GPIO level from
    // triggering wake from lightsleep, it just won't call this ISR.
    gpio_intr_disable(gpio);

    // In the interests of consistency, also stop the GPIO from triggering wakeup
    gpio_wakeup_disable(gpio);

    // Following is as per machine_pin_isr_handler
    mp_obj_t handler = MP_STATE_PORT(machine_pin_irq_handler)[gpio];
    mp_sched_schedule(handler, MP_OBJ_NEW_SMALL_INT(gpio));
    mp_hal_wake_main_task_from_isr();
}

// tidal_helpers.set_lightsleep_irq(Pin|int, level, handler) or
// tidal_helpers.set_lightsleep_irq(Pin|int, None, None) to disable
STATIC mp_obj_t tidal_set_lightsleep_irq(mp_obj_t gpio_obj, mp_obj_t level_obj, mp_obj_t handler) {
    gpio_num_t gpio = get_pin(gpio_obj);

    // This disables the interrupt as the first thing it does
    esp_err_t err = gpio_isr_handler_remove(gpio);
    check_esp_err(err);

    if (handler == mp_const_none) {
        gpio_wakeup_disable(gpio);
        // Return with interrupt disabled and no ISR or wake enabled
        return mp_const_none;
    }

    // Stash handler in machine state, as a convenient place to put it
    MP_STATE_PORT(machine_pin_irq_handler)[gpio] = handler;

    int level = mp_obj_get_int(level_obj);
    // Configure wake params - note this includes (the equivalent to) a call to
    // gpio_set_intr_type. Interrupt remains disabled.
    err = gpio_wakeup_enable(gpio, level ? GPIO_INTR_HIGH_LEVEL : GPIO_INTR_LOW_LEVEL);
    check_esp_err(err);

    // Finally, install ISR handler and enable interrupt.
    err = gpio_isr_handler_add(gpio, tidal_lightsleep_isr, (void *)gpio);
    check_esp_err(err);

    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_3(tidal_set_lightsleep_irq_obj, tidal_set_lightsleep_irq);

STATIC mp_obj_t tidal_gpio_intr_enable(mp_obj_t gpio_obj, mp_obj_t flag_obj) {
    gpio_num_t gpio = get_pin(gpio_obj);
    bool flag = mp_obj_is_true(flag_obj);
    esp_err_t err;
    if (flag) {
        err = gpio_intr_enable(gpio);
    } else {
        err = gpio_intr_disable(gpio);
    }
    check_esp_err(err);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(tidal_gpio_intr_enable_obj, tidal_gpio_intr_enable);

STATIC mp_obj_t tidal_gpio_sleep_sel(mp_obj_t gpio_obj, mp_obj_t flag_obj) {
    gpio_num_t gpio = get_pin(gpio_obj);
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

STATIC mp_obj_t tidal_uart_tx_flush(mp_obj_t id_obj) {
    int id = mp_obj_get_int(id_obj);
    uart_tx_flush(id);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_uart_tx_flush_obj, tidal_uart_tx_flush);

STATIC mp_obj_t tidal_lightsleep(mp_obj_t time_obj) {
    int time_ms = mp_obj_get_int(time_obj);
    if (time_ms) {
        esp_sleep_enable_timer_wakeup(((uint64_t)time_ms) * 1000);
    }

    esp_light_sleep_start();

    if (time_ms) {
        // Reset this
        esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER);
    }

    return MP_OBJ_NEW_SMALL_INT(esp_sleep_get_wakeup_cause());
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_lightsleep_obj, tidal_lightsleep);

STATIC const mp_rom_map_elem_t tidal_helpers_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ota) },
    { MP_ROM_QSTR(MP_QSTR_get_variant), MP_ROM_PTR(&tidal_helper_get_variant_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_sleep_enable_gpio_wakeup), MP_ROM_PTR(&tidal_esp_sleep_enable_gpio_wakeup_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_sleep_pd_config), MP_ROM_PTR(&tidal_esp_sleep_pd_config_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_wakeup), MP_ROM_PTR(&tidal_gpio_wakeup_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_lightsleep_irq), MP_ROM_PTR(&tidal_set_lightsleep_irq_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_hold), MP_ROM_PTR(&tidal_gpio_hold_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_intr_enable), MP_ROM_PTR(&tidal_gpio_intr_enable_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_sleep_sel), MP_ROM_PTR(&tidal_gpio_sleep_sel_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_sleep_enable_gpio_switch), MP_ROM_PTR(&tidal_esp_sleep_enable_gpio_switch_obj) },
    { MP_ROM_QSTR(MP_QSTR_uart_tx_flush), MP_ROM_PTR(&tidal_uart_tx_flush_obj) },
    { MP_ROM_QSTR(MP_QSTR_lightsleep), MP_ROM_PTR(&tidal_lightsleep_obj) },

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
