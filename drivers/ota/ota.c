#include "py/runtime.h"
#include "esp_log.h"
#include "sdkconfig.h"
#include "mphalport.h"
#include "esp_ota_ops.h"
#include "esp_https_ota.h"

#include "esp_sleep.h"

static const char *TAG = "ota";

#define IMAGE_URL "https://raw.githubusercontent.com/tomsci/tidal-ota/main/micropython.bin"

// openssl x509 -text -inform DER -in "DigiCert Global Root CA.cer"
static const char kGithubCertificate[] =
    "-----BEGIN CERTIFICATE-----\n"
    "MIIDrzCCApegAwIBAgIQCDvgVpBCRrGhdWrJWZHHSjANBgkqhkiG9w0BAQUFADBh\n"
    "MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3\n"
    "d3cuZGlnaWNlcnQuY29tMSAwHgYDVQQDExdEaWdpQ2VydCBHbG9iYWwgUm9vdCBD\n"
    "QTAeFw0wNjExMTAwMDAwMDBaFw0zMTExMTAwMDAwMDBaMGExCzAJBgNVBAYTAlVT\n"
    "MRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxGTAXBgNVBAsTEHd3dy5kaWdpY2VydC5j\n"
    "b20xIDAeBgNVBAMTF0RpZ2lDZXJ0IEdsb2JhbCBSb290IENBMIIBIjANBgkqhkiG\n"
    "9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4jvhEXLeqKTTo1eqUKKPC3eQyaKl7hLOllsB\n"
    "CSDMAZOnTjC3U/dDxGkAV53ijSLdhwZAAIEJzs4bg7/fzTtxRuLWZscFs3YnFo97\n"
    "nh6Vfe63SKMI2tavegw5BmV/Sl0fvBf4q77uKNd0f3p4mVmFaG5cIzJLv07A6Fpt\n"
    "43C/dxC//AH2hdmoRBBYMql1GNXRor5H4idq9Joz+EkIYIvUX7Q6hL+hqkpMfT7P\n"
    "T19sdl6gSzeRntwi5m3OFBqOasv+zbMUZBfHWymeMr/y7vrTC0LUq7dBMtoM1O/4\n"
    "gdW7jVg/tRvoSSiicNoxBN33shbyTApOB6jtSj1etX+jkMOvJwIDAQABo2MwYTAO\n"
    "BgNVHQ8BAf8EBAMCAYYwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUA95QNVbR\n"
    "TLtm8KPiGxvDl7I90VUwHwYDVR0jBBgwFoAUA95QNVbRTLtm8KPiGxvDl7I90VUw\n"
    "DQYJKoZIhvcNAQEFBQADggEBAMucN6pIExIK+t1EnE9SsPTfrgT1eXkIoyQY/Esr\n"
    "hMAtudXH/vTBH1jLuG2cenTnmCmrEbXjcKChzUyImZOMkXDiqw8cvpOp/2PV5Adg\n"
    "06O/nVsJ8dWO41P0jmP6P6fbtGbfYmbW0W5BjfIttep3Sp+dWOIrWcBAI+0tKIJF\n"
    "PnlUkiaY4IBIqDfv8NZ5YBberOgOzW6sRBc4L0na4UU+Krk2U886UAb3LujEV0ls\n"
    "YSEY1QSteDwsOoBrp+uvFRTp2InBuThs4pFsiv9kuXclVzDAGySj4dzp30d8tbQk\n"
    "CAUw7C29C79Fv1C5qfPrmAESrciIxpg0X40KPMbp1ZWVbd4=\n"
    "-----END CERTIFICATE-----\n";

STATIC mp_obj_t ota_update(mp_obj_t cb_obj) {
    esp_http_client_config_t config = {
        .url = IMAGE_URL,
        .cert_pem = kGithubCertificate,
    };
    esp_https_ota_config_t ota_config = {
        .http_config = &config,
    };

    esp_https_ota_handle_t handle;
    esp_err_t err = esp_https_ota_begin(&ota_config, &handle);
    check_esp_err(err);

    const int sz = esp_https_ota_get_image_size(handle);
    int count = 0;
    int last_progress = -1;

    esp_app_desc_t info = {0};
    err = esp_https_ota_get_img_desc(handle, &info);
    check_esp_err(err);
    mp_obj_t version = mp_obj_new_str(info.version, strlen(info.version));

    int aborted = 0;
    while (!aborted) {
        err = esp_https_ota_perform(handle);
        if (err == ESP_ERR_HTTPS_OTA_IN_PROGRESS) {
            count = esp_https_ota_get_image_len_read(handle);
            int progress = (count * 100) / sz;
            if (progress > last_progress) {
                mp_obj_t progress_obj = mp_obj_new_int(progress);
                aborted = !mp_obj_is_true(mp_call_function_2(cb_obj, version, progress_obj));
            }
        } else {
            break;
        }
    }

    if (err == ESP_OK && !aborted) {
        mp_call_function_2(cb_obj, version, mp_obj_new_int(100));
        err = esp_https_ota_finish(handle);
    } else {
        esp_https_ota_abort(handle);
    }
    if (!aborted) {
        check_esp_err(err);
    }

    // Return true if updated
    return mp_obj_new_bool(!aborted);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ota_update_obj, ota_update);

STATIC mp_obj_t ota_get_version() {
    esp_app_desc_t info = {0};
    const esp_partition_t *p = esp_ota_get_running_partition();
    esp_err_t err = esp_ota_get_partition_description(p, &info);
    check_esp_err(err);
    return mp_obj_new_str(info.version, strlen(info.version));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(ota_get_version_obj, ota_get_version);

// TODO move this to tidal_helpers

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
    int flag = (gpio_int_type_t)mp_obj_is_true(flag_obj);
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

STATIC const mp_rom_map_elem_t ota_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ota) },
    { MP_ROM_QSTR(MP_QSTR_update), MP_ROM_PTR(&ota_update_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_version), MP_ROM_PTR(&ota_get_version_obj) },

    { MP_ROM_QSTR(MP_QSTR_esp_sleep_enable_gpio_wakeup), MP_ROM_PTR(&tidal_esp_sleep_enable_gpio_wakeup_obj) },
    { MP_ROM_QSTR(MP_QSTR_esp_sleep_pd_config), MP_ROM_PTR(&tidal_esp_sleep_pd_config_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_wakeup), MP_ROM_PTR(&tidal_gpio_wakeup_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_hold), MP_ROM_PTR(&tidal_gpio_hold_obj) },
    { MP_ROM_QSTR(MP_QSTR_gpio_sleep_sel), MP_ROM_PTR(&tidal_gpio_sleep_sel_obj) },

    { MP_ROM_QSTR(MP_QSTR_ESP_PD_DOMAIN_RTC_PERIPH), MP_ROM_INT(ESP_PD_DOMAIN_RTC_PERIPH) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_OPTION_OFF), MP_ROM_INT(ESP_PD_OPTION_OFF) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_OPTION_ON), MP_ROM_INT(ESP_PD_OPTION_ON) },
    { MP_ROM_QSTR(MP_QSTR_ESP_PD_OPTION_AUTO), MP_ROM_INT(ESP_PD_OPTION_AUTO) },
};
STATIC MP_DEFINE_CONST_DICT(ota_module_globals, ota_module_globals_table);

const mp_obj_module_t ota_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&ota_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_ota, ota_user_cmodule, 1);
