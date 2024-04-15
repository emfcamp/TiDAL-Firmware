#include "py/runtime.h"
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

// static const char *TAG = "tidal_helpers";

// Have to redefine this from machine_pin.c, unfortunately
typedef struct _machine_pin_obj_t {
    mp_obj_base_t base;
    gpio_num_t id;
} machine_pin_obj_t;

STATIC mp_obj_t tidal_helper_authentication_operation() {
    return mp_obj_new_int(authentication_operation);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_helper_authentication_operation_obj, tidal_helper_authentication_operation);

STATIC mp_obj_t tidal_helper_authentication_requested() {
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
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_helper_authentication_requested_obj, tidal_helper_authentication_requested);

STATIC mp_obj_t tidal_helper_authentication_mismatch() {
    authentication_operation = KEY_MISMATCH;
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_helper_authentication_mismatch_obj, tidal_helper_authentication_mismatch);

STATIC mp_obj_t tidal_helper_authentication_approve(mp_obj_t state) {
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
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_helper_authentication_approve_obj, tidal_helper_authentication_approve);


STATIC mp_obj_t tidal_helper_authentication_slot(mp_obj_t slot) {
    if (mp_obj_is_int(slot)) {
        authentication_operation_slot = mp_obj_get_int(slot);
        return slot;
    } else {
        mp_raise_ValueError(slot);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_helper_authentication_slot_obj, tidal_helper_authentication_slot);


STATIC gpio_num_t get_pin(mp_obj_t pin_obj) {
    if (mp_obj_is_int(pin_obj)) {
        return (gpio_num_t)mp_obj_get_int(pin_obj);
    } else if (mp_obj_get_type(pin_obj) != &machine_pin_type) {
        mp_raise_ValueError(MP_ERROR_TEXT("expecting a pin or integer pin number"));
    }
    machine_pin_obj_t *self = pin_obj;
    return self->id;
}

void reboot_bootloader() {
    usb_dc_prepare_persist();
    chip_usb_set_persist_flags(USBDC_PERSIST_ENA);
    REG_WRITE(RTC_CNTL_OPTION1_REG, RTC_CNTL_FORCE_DOWNLOAD_BOOT);
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

// usb_connected() -> bool : Returns True if any USB packets have been received since last usb reset
STATIC mp_obj_t tidal_helper_usb_connected() {
    if (tud_connected())
        return mp_const_true;
    else
        return mp_const_false;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_helper_usb_connected_obj, tidal_helper_usb_connected);

STATIC mp_obj_t tidal_helper_usb_suspended() {
    return tud_suspended() ? mp_const_true : mp_const_false;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_helper_usb_suspended_obj, tidal_helper_usb_suspended);

STATIC mp_obj_t tidal_helper_usb_mounted() {
    return tud_mounted() ? mp_const_true : mp_const_false;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_helper_usb_mounted_obj, tidal_helper_usb_mounted);

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

    // Following is based on machine_pin_isr_handler
    mp_obj_t handler = MP_STATE_PORT(machine_pin_irq_handler)[gpio];
    if (handler == mp_const_none || handler == MP_OBJ_NULL) {
        // It shouldn't be possible to get to here with handler not valid, but...
        return;
    }
    // Give py code an indication what interrupt fired (and thus needs resetting) by nulling the handler
    MP_STATE_PORT(machine_pin_irq_handler)[gpio] = mp_const_none;

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
STATIC mp_obj_t tidal_helper_reboot_bootloader() {
    esp_register_shutdown_handler(reboot_bootloader);
    esp_restart();
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(tidal_helper_reboot_bootloader_obj, tidal_helper_reboot_bootloader);


STATIC mp_obj_t tidal_get_irq_handler(mp_obj_t gpio_obj) {
    gpio_num_t gpio = get_pin(gpio_obj);
    mp_obj_t handler = MP_STATE_PORT(machine_pin_irq_handler)[gpio];
    if (handler == MP_OBJ_NULL) {
        handler = mp_const_none;
    }
    return handler;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_get_irq_handler_obj, tidal_get_irq_handler);

STATIC mp_obj_t tidal_pin_number(mp_obj_t gpio_obj) {
    gpio_num_t gpio = get_pin(gpio_obj);
    return MP_OBJ_NEW_SMALL_INT(gpio);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_pin_number_obj, tidal_pin_number);

STATIC mp_obj_t tidal_esp_wifi_set_max_tx_power(mp_obj_t pwr_obj) {
    int8_t pwr = mp_obj_get_int(pwr_obj);
    esp_err_t err = esp_wifi_set_max_tx_power(pwr);
    check_esp_err(err);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_esp_wifi_set_max_tx_power_obj, tidal_esp_wifi_set_max_tx_power);

STATIC mp_obj_t tidal_esp_wifi_sta_wpa2_ent_enable(mp_obj_t flag_obj) {
    esp_err_t err;
    if (mp_obj_is_true(flag_obj)) {
        err = esp_wifi_sta_wpa2_ent_enable();
    } else {
        err = esp_wifi_sta_wpa2_ent_disable();
    }
    check_esp_err(err);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_esp_wifi_sta_wpa2_ent_enable_obj, tidal_esp_wifi_sta_wpa2_ent_enable);

STATIC mp_obj_t tidal_esp_wifi_sta_wpa2_ent_set_identity(mp_obj_t id_obj) {
    if (mp_obj_is_true(id_obj)) {
        size_t len = 0;
        const char* id = mp_obj_str_get_data(id_obj, &len);
        esp_err_t err = esp_wifi_sta_wpa2_ent_set_identity((const unsigned char*)id, len);
        check_esp_err(err);
    } else {
        esp_wifi_sta_wpa2_ent_clear_identity();
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_esp_wifi_sta_wpa2_ent_set_identity_obj, tidal_esp_wifi_sta_wpa2_ent_set_identity);

STATIC mp_obj_t tidal_esp_wifi_sta_wpa2_ent_set_username(mp_obj_t username_obj) {
    if (mp_obj_is_true(username_obj)) {
        size_t len = 0;
        const char* username = mp_obj_str_get_data(username_obj, &len);
        esp_err_t err = esp_wifi_sta_wpa2_ent_set_username((const unsigned char*)username, len);
        check_esp_err(err);
    } else {
        esp_wifi_sta_wpa2_ent_clear_username();
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_esp_wifi_sta_wpa2_ent_set_username_obj, tidal_esp_wifi_sta_wpa2_ent_set_username);

STATIC mp_obj_t tidal_esp_wifi_sta_wpa2_ent_set_password(mp_obj_t pass_obj) {
    if (mp_obj_is_true(pass_obj)) {
        size_t len = 0;
        const char* password = mp_obj_str_get_data(pass_obj, &len);
        esp_err_t err = esp_wifi_sta_wpa2_ent_set_password((const unsigned char*)password, len);
        check_esp_err(err);
    } else {
        esp_wifi_sta_wpa2_ent_clear_password();
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(tidal_esp_wifi_sta_wpa2_ent_set_password_obj, tidal_esp_wifi_sta_wpa2_ent_set_password);

// We're hard coding these, meaning there's a risk of overlap if anyone tries to
// use the machine.PWM micropython class. But, the esp32s3 requirements on all
// timers having to use the same clock source means any other users already have
// to be aware of what we're doing here to not break things, so I don't feel too
// bad about going behind micropython's back in this way. And the only reason
// we're not using machine.PWM here is that the micropython API does't let us
// configure the LEDC_USE_RTC8M_CLK clock which is essential to work in light
// sleep.
static const ledc_channel_t kBacklightChannel = LEDC_CHANNEL_7;
static const ledc_timer_t kBacklightTimer = LEDC_TIMER_3;

STATIC mp_obj_t tidal_set_backlight_pwm(mp_obj_t gpio_obj, mp_obj_t val_obj) {
    gpio_num_t gpio = get_pin(gpio_obj);
    esp_err_t err = 0;
    if (val_obj == mp_const_none) {
        // NOTE(tomsci): Just copying what machine_pwm.c does here...
        err = ledc_timer_rst(LEDC_LOW_SPEED_MODE, kBacklightTimer);
        if (err == ESP_ERR_INVALID_STATE) {
            // Then it's never been set up, so nothing needed
            return mp_const_none;
        }
        check_esp_err(err);
        err = ledc_stop(LEDC_LOW_SPEED_MODE, kBacklightChannel, 0);
        check_esp_err(err);
        // Disable ledc signal for the pin
        gpio_matrix_out(gpio, LEDC_LS_SIG_OUT0_IDX + kBacklightChannel, false, true);

        // And finally, we can disable the RTC8 clock in lightsleep
        err = esp_sleep_pd_config(ESP_PD_DOMAIN_RTC8M, ESP_PD_OPTION_OFF);
        check_esp_err(err);

        // I'm not sure why this is necessary, but it seems to be...
        err = gpio_set_direction(gpio, GPIO_MODE_OUTPUT);
        check_esp_err(err);

        return mp_const_none;
    }

    ledc_channel_config_t channel_cfg = {
        .gpio_num = gpio,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = kBacklightChannel,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = kBacklightTimer,
        .duty = mp_obj_get_int(val_obj),
    };
    err = ledc_channel_config(&channel_cfg);
    check_esp_err(err);

    ledc_timer_config_t timer_cfg = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_14_BIT,
        .timer_num = kBacklightTimer,
        .freq_hz = 100,
        .clk_cfg = LEDC_USE_RTC8M_CLK, // This is the only clock that can run in lightsleep
    };

    err = ledc_timer_config(&timer_cfg);
    check_esp_err(err);

    // This is needed to keep the clock running in lightsleep
    err = esp_sleep_pd_config(ESP_PD_DOMAIN_RTC8M, ESP_PD_OPTION_ON);
    check_esp_err(err);

    return mp_const_none;

}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(tidal_set_backlight_pwm_obj, tidal_set_backlight_pwm);

STATIC const mp_rom_map_elem_t tidal_helpers_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ota) },
    { MP_ROM_QSTR(MP_QSTR_get_authentication_operation), MP_ROM_PTR(&tidal_helper_authentication_operation_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_authentication_approval), MP_ROM_PTR(&tidal_helper_authentication_approve_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_authentication_requested), MP_ROM_PTR(&tidal_helper_authentication_requested_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_authentication_mismatch), MP_ROM_PTR(&tidal_helper_authentication_mismatch_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_authentication_slot), MP_ROM_PTR(&tidal_helper_authentication_slot_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_variant), MP_ROM_PTR(&tidal_helper_get_variant_obj) },
    { MP_ROM_QSTR(MP_QSTR_usb_connected), MP_ROM_PTR(&tidal_helper_usb_connected_obj) },
    { MP_ROM_QSTR(MP_QSTR_usb_suspended), MP_ROM_PTR(&tidal_helper_usb_suspended_obj) },
    { MP_ROM_QSTR(MP_QSTR_usb_mounted), MP_ROM_PTR(&tidal_helper_usb_mounted_obj) },
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
    { MP_ROM_QSTR(MP_QSTR_get_irq_handler), MP_ROM_PTR(&tidal_get_irq_handler_obj) },
    { MP_ROM_QSTR(MP_QSTR_pin_number), MP_ROM_PTR(&tidal_pin_number_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_wifi_set_max_tx_power), MP_ROM_PTR(&tidal_esp_wifi_set_max_tx_power_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_wifi_sta_wpa2_ent_enable), MP_ROM_PTR(&tidal_esp_wifi_sta_wpa2_ent_enable_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_wifi_sta_wpa2_ent_set_identity), MP_ROM_PTR(&tidal_esp_wifi_sta_wpa2_ent_set_identity_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_wifi_sta_wpa2_ent_set_username), MP_ROM_PTR(&tidal_esp_wifi_sta_wpa2_ent_set_username_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_wifi_sta_wpa2_ent_set_password), MP_ROM_PTR(&tidal_esp_wifi_sta_wpa2_ent_set_password_obj) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_DOMAIN_RTC_PERIPH), MP_ROM_INT(ESP_PD_DOMAIN_RTC_PERIPH) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_DOMAIN_RTC8M), MP_ROM_INT(ESP_PD_DOMAIN_RTC8M) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_OPTION_OFF), MP_ROM_INT(ESP_PD_OPTION_OFF) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_OPTION_ON), MP_ROM_INT(ESP_PD_OPTION_ON) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_OPTION_AUTO), MP_ROM_INT(ESP_PD_OPTION_AUTO) },
    { MP_ROM_QSTR(MP_QSTR_reboot_bootloader), MP_ROM_PTR(&tidal_helper_reboot_bootloader_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_backlight_pwm), MP_ROM_PTR(&tidal_set_backlight_pwm_obj) },
};
STATIC MP_DEFINE_CONST_DICT(tidal_helpers_module_globals, tidal_helpers_module_globals_table);

const mp_obj_module_t tidal_helpers_user_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&tidal_helpers_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_tidal_helpers, tidal_helpers_user_module, 1);
