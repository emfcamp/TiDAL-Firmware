#include <stdio.h>
#include <string.h>
#include <driver/i2c.h>
#include "extmod/machine_i2c.h"
#include "ports/esp32/modmachine.h"
#include "esp_err.h"
#include "esp_log.h"
#include "cryptoauthlib.h"
#include "py/runtime.h"

#define SCL_S                              41
#define SDA_S                              42

const char* TAG = "HAL_SOFTI2C";

/* For debugging on the production board over USB */
#define HAL_SOFTI2C_DEBUG 0
#define hal_softi2c_debug_print(fmt, ...) \
            do { if (HAL_SOFTI2C_DEBUG) mp_printf(fmt, __VA_ARGS__); } while (0)


/** \brief method to change the bus speed of I2C
 * \param[in] iface  interface on which to change bus speed
 * \param[in] speed  baud rate (typically 100000 or 400000)
 */
ATCA_STATUS hal_i2c_change_baud(ATCAIface iface, uint32_t speed)
{
    // FIXME: implement
    return ATCA_SUCCESS;
}

ATCA_STATUS hal_i2c_init(ATCAIface iface, ATCAIfaceCfg *cfg)
{
    hal_softi2c_debug_print(&mp_plat_print, "hal_i2c_init\n");

    // FIXME: read cfg

    mp_obj_t pin_scl = mp_obj_new_int(SCL_S);
    mp_obj_t pin_sda = mp_obj_new_int(SDA_S);
    mp_obj_t args[] = {
        machine_pin_type.make_new(&machine_pin_type, 1, 0, &pin_scl),
        machine_pin_type.make_new(&machine_pin_type, 1, 0, &pin_sda),
        /* following is actually mp_map_elem_t[] */
        MP_ROM_QSTR(MP_QSTR_freq), mp_obj_new_int(100000),
    };
    mp_obj_t i2c = mp_machine_soft_i2c_type.make_new(&mp_machine_soft_i2c_type, 2, 1, args);
    hal_softi2c_debug_print(&mp_plat_print, "SoftI2C(pin_scl, pin_sda, freq=freq) returned 0x%x\n", i2c);
    iface->hal_data = (void *) i2c;

    return ATCA_SUCCESS;
}

/** \brief HAL implementation of I2C post init
 * \param[in] iface  instance
 * \return ATCA_SUCCESS
 */
ATCA_STATUS hal_i2c_post_init(ATCAIface iface)
{
    return ATCA_SUCCESS;
}

/** \brief HAL implementation of I2C send
 * \param[in] iface         instance
 * \param[in] word_address  device transaction type
 * \param[in] txdata        pointer to space to bytes to send
 * \param[in] txlength      number of bytes to send
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */
ATCA_STATUS hal_i2c_send(ATCAIface iface, uint8_t address, uint8_t *txdata, int txlength)
{
    hal_softi2c_debug_print(&mp_plat_print, "hal_i2c_send\n");
    mp_obj_base_t *i2c = (mp_obj_base_t *) iface->hal_data;
    mp_machine_i2c_p_t *i2c_p = (mp_machine_i2c_p_t *) mp_machine_soft_i2c_type.protocol;

    mp_machine_i2c_buf_t buf = {.len = txlength, .buf = (uint8_t *)txdata};
    int acks = i2c_p->transfer(i2c, address, 1, &buf, MP_MACHINE_I2C_FLAG_STOP);
    hal_softi2c_debug_print(&mp_plat_print, "i2c.transfer returned 0x%x\n", acks);
    if (acks < 0) {
        return acks;
    }
    return ATCA_SUCCESS;
}

/** \brief HAL implementation of I2C receive function
 * \param[in]    iface          Device to interact with.
 * \param[in]    address        Device address
 * \param[out]   rxdata         Data received will be returned here.
 * \param[in,out] rxlength      As input, the size of the rxdata buffer.
 *                              As output, the number of bytes received.
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */
ATCA_STATUS hal_i2c_receive(ATCAIface iface, uint8_t address, uint8_t *rxdata, uint16_t *rxlength)
{
    hal_softi2c_debug_print(&mp_plat_print, "hal_i2c_receive\n");
    mp_obj_base_t *i2c = (mp_obj_base_t *) iface->hal_data;
    mp_machine_i2c_p_t *i2c_p = (mp_machine_i2c_p_t *) mp_machine_soft_i2c_type.protocol;

    mp_machine_i2c_buf_t buf = {.len = *rxlength, .buf = rxdata};
    int status = i2c_p->transfer(i2c, address, 1, &buf, MP_MACHINE_I2C_FLAG_READ | MP_MACHINE_I2C_FLAG_STOP);
    hal_softi2c_debug_print(&mp_plat_print, "i2c.transfer returned 0x%x\n", status);
    if (status < 0) {
        return status;
    }
    // rxlength will be the number of bytes received
    return ATCA_SUCCESS;
}

/** \brief manages reference count on given bus and releases resource if no more refences exist
 * \param[in] hal_data - opaque pointer to hal data structure - known only to the HAL implementation
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */
ATCA_STATUS hal_i2c_release(void *hal_data)
{
    hal_softi2c_debug_print(&mp_plat_print, "hal_i2c_release\n");
    mp_obj_base_t *i2c = (mp_obj_base_t *) hal_data;
    // FIXME: delete i2c
    return ATCA_SUCCESS;
}

/** \brief Perform control operations for the kit protocol
 * \param[in]     iface          Interface to interact with.
 * \param[in]     option         Control parameter identifier
 * \param[in]     param          Optional pointer to parameter value
 * \param[in]     paramlen       Length of the parameter
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */
ATCA_STATUS hal_i2c_control(ATCAIface iface, uint8_t option, void* param, size_t paramlen)
{
    hal_softi2c_debug_print(&mp_plat_print, "hal_i2c_control\n");
    mp_obj_base_t *i2c = (mp_obj_base_t *) iface->hal_data;
    return ATCA_UNIMPLEMENTED;
}
