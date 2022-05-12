// From badge.team: https://github.com/badgeteam/ESP32-platform-firmware/tree/master/firmware/components/driver_rtcmem

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "sdkconfig.h"
#include "esp_log.h"
#include "rom/crc.h"
#include "py/runtime.h"

#include <esp_log.h>
#include <esp_err.h>

#include "include/driver_rtcmem.h"

#define TAG "rtcmem"

#define RTC_MEM_INT_SIZE 64
#define RTC_MEM_STR_SIZE 2048

static int      RTC_NOINIT_ATTR rtc_mem_int[RTC_MEM_INT_SIZE] = { 0 };
static uint16_t RTC_NOINIT_ATTR rtc_mem_int_crc;

static char     RTC_NOINIT_ATTR rtc_mem_str[RTC_MEM_STR_SIZE] = { 0 };
static uint16_t RTC_NOINIT_ATTR rtc_mem_str_crc;

esp_err_t driver_rtcmem_int_write(int pos, int val)
{
	if (pos >= RTC_MEM_INT_SIZE) return ESP_FAIL;
	rtc_mem_int[pos] = val;
	rtc_mem_int_crc = crc16_le(0, (uint8_t const *)rtc_mem_int, RTC_MEM_INT_SIZE*sizeof(int));
	return ESP_OK;
}

esp_err_t driver_rtcmem_int_read(int pos, int* val)
{
	if (pos >= RTC_MEM_INT_SIZE) return ESP_FAIL;
	if (rtc_mem_int_crc != crc16_le(0, (uint8_t const *)rtc_mem_int, RTC_MEM_INT_SIZE*sizeof(int))) return ESP_FAIL;
	*val = rtc_mem_int[pos];
	return ESP_OK;
}

esp_err_t driver_rtcmem_string_write(const char* str)
{
	if (strlen(str) >= RTC_MEM_STR_SIZE) return ESP_FAIL;
	memset(rtc_mem_str, 0, sizeof(rtc_mem_str));
	strcpy(rtc_mem_str, str);
	rtc_mem_str_crc = crc16_le(0, (uint8_t const *)rtc_mem_str, RTC_MEM_STR_SIZE);
	return ESP_OK;
}

esp_err_t driver_rtcmem_string_read(const char** str)
{
	if (rtc_mem_str_crc != crc16_le(0, (uint8_t const *)rtc_mem_str, RTC_MEM_STR_SIZE)) return ESP_FAIL;
	*str = rtc_mem_str;
	return ESP_OK;
}

esp_err_t driver_rtcmem_clear()
{
	memset(rtc_mem_int, 0, sizeof(rtc_mem_int));
	memset(rtc_mem_str, 0, sizeof(rtc_mem_str));
	rtc_mem_int_crc = 0;
	rtc_mem_str_crc = 0;
	return ESP_OK;
}

esp_err_t driver_rtcmem_init(void)
{
	//Empty
	return ESP_OK;
}


//--------------------------------------------------------------------------------
STATIC mp_obj_t esp_rtcmem_write(mp_obj_t _pos, mp_obj_t _val) {
	int pos = mp_obj_get_int(_pos);
	int val = mp_obj_get_int(_val);
	if (driver_rtcmem_int_write(pos, val) != ESP_OK) return mp_const_false;
	return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(esp_rtcmem_write_obj, esp_rtcmem_write);

//----------------------------------------------------------------
STATIC mp_obj_t esp_rtcmem_read(mp_obj_t _pos) {
	int pos = mp_obj_get_int(_pos);
	int value;
	if (driver_rtcmem_int_read(pos, &value) != ESP_OK) return mp_const_none;	
	return mp_obj_new_int(value);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(esp_rtcmem_read_obj, esp_rtcmem_read);

//--------------------------------------------------------------------------
STATIC mp_obj_t esp_rtcmem_write_string(mp_obj_t str_in) {
	const char *str = mp_obj_str_get_str(str_in);
	if (driver_rtcmem_string_write(str) != ESP_OK) return mp_const_false;
	return mp_const_true;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(esp_rtcmem_write_string_obj, esp_rtcmem_write_string);

//--------------------------------------------------------
STATIC mp_obj_t esp_rtcmem_read_string() {
	const char* str;
	if (driver_rtcmem_string_read(&str) != ESP_OK) return mp_const_none;
	return mp_obj_new_str(str, strlen(str));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(esp_rtcmem_read_string_obj, esp_rtcmem_read_string);

//--------------------------------------------------
STATIC mp_obj_t esp_rtcmem_clear() {
    driver_rtcmem_clear();
	return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(esp_rtcmem_clear_obj, esp_rtcmem_clear);



//=========================================================
STATIC const mp_rom_map_elem_t rtcmem_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), 			MP_ROM_QSTR(MP_QSTR_rtcmem) },
    { MP_OBJ_NEW_QSTR(MP_QSTR_write),			(mp_obj_t)&esp_rtcmem_write_obj},
    { MP_OBJ_NEW_QSTR(MP_QSTR_read),			(mp_obj_t)&esp_rtcmem_read_obj},
    { MP_OBJ_NEW_QSTR(MP_QSTR_clear),			(mp_obj_t)&esp_rtcmem_clear_obj},
    { MP_OBJ_NEW_QSTR(MP_QSTR_write_string),	(mp_obj_t)&esp_rtcmem_write_string_obj},
    { MP_OBJ_NEW_QSTR(MP_QSTR_read_string),		(mp_obj_t)&esp_rtcmem_read_string_obj},
    };
STATIC MP_DEFINE_CONST_DICT(rtcmem_module_globals, rtcmem_module_globals_table);


const mp_obj_module_t rtcmem_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&rtcmem_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_rtcmem, rtcmem_module, 1);
