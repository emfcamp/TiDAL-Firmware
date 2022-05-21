#define LODEPNG_NO_COMPILE_ALLOCATORS
#include "../../lodepng/lodepng.cpp"

#include "py/runtime.h"
#include "py/objarray.h"
#include "esp_log.h"

static const char *TAG = "lodepng";

void* lodepng_malloc(size_t size) {
    return m_malloc(size);
}

void* lodepng_realloc(void* ptr, size_t new_size) {
    return m_realloc(ptr, new_size);
}

void lodepng_free(void* ptr) {
    m_free(ptr);
}

// STATIC uint16_t color565(uint8_t r, uint8_t g, uint8_t b)
// {
//     return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3);
// }

STATIC mp_obj_t lodepng_decode_565(mp_obj_t obj) {
    size_t len = 0;
    const char* inbuf = NULL;

    if (mp_obj_is_str(obj)) {
        // Assume it's a path. Why we can't just fopen these (like lodepng tries
        // to do) I don't know :-(
        mp_obj_t open_obj = mp_load_global(MP_QSTR_open);
        mp_obj_t f = mp_call_function_2(open_obj, obj, MP_OBJ_NEW_QSTR(MP_QSTR_rb));
        mp_obj_t fn;
        mp_load_method(f, MP_QSTR_read, &fn);
        mp_obj_t buf_obj = mp_call_method_n_kw(0, 0, &fn);
        mp_load_method(f, MP_QSTR_close, &fn);
        mp_call_method_n_kw(0, 0, &fn);
        inbuf = mp_obj_str_get_data(buf_obj, &len);
    } else if (mp_obj_is_type(obj, &mp_type_memoryview)) {
        mp_obj_array_t *arr = MP_OBJ_TO_PTR(obj);
        len = arr->len;
        inbuf = arr->items;
    } else {
        inbuf = mp_obj_str_get_data(obj, &len);
    }

    unsigned char* buf = NULL;
    unsigned w, h;
    unsigned err = lodepng_decode24(&buf, &w, &h, (const unsigned char*)inbuf, len);

    if (err) {
        ESP_LOGE(TAG, "lodepng_decode24 returned %u", err);
        return mp_const_none;
    }

    // in-place convert RGB 888 to 565
    unsigned char* outptr = buf;
    const int imax = w * 3;
    for (int y = 0; y < h; y++) {
        unsigned char* rowptr = (unsigned char*)buf + (y * w * 3);
        for (int i = 0; i < imax; i += 3) {
            uint8_t r = rowptr[i];
            uint8_t g = rowptr[i+1];
            uint8_t b = rowptr[i+2];
            *outptr++ = (r & 0xF8) | (g >> 5);
            *outptr++ = (g << 5) | ((b & 0xF8) >> 3);
        }
    }

    mp_obj_t result[3];
    result[0] = MP_OBJ_NEW_SMALL_INT(w);
    result[1] = MP_OBJ_NEW_SMALL_INT(h);

    // Since we configure lodepng to use micropython's allocator, we can turn
    // buf into a python object without having to alloc another buffer.
    size_t sz = w * h * 2;
    buf = m_realloc(buf, sz); // Since it was originally sized for 888 RGB ie w*h*3
    result[2] = mp_obj_new_bytearray_by_ref(sz, buf);
    return mp_obj_new_tuple(3, result);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(lodepng_decode_565_obj, lodepng_decode_565);

STATIC const mp_rom_map_elem_t lodepng_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_lodepng) },
    { MP_ROM_QSTR(MP_QSTR_decode565), MP_ROM_PTR(&lodepng_decode_565_obj) },
};
STATIC MP_DEFINE_CONST_DICT(lodepng_module_globals, lodepng_module_globals_table);

const mp_obj_module_t lodepng_user_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&lodepng_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_lodepng, lodepng_user_module, 1);
