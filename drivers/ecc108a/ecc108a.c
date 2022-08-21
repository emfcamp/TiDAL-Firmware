#include "py/runtime.h"
#include "atca_iface.h"
#include "atca_basic.h"

struct SlotConfig {
    uint16_t ReadKey            : 4;
    uint16_t NoMac              : 1;
    uint16_t LimitedUse         : 1;
    uint16_t EncryptRead        : 1;
    uint16_t IsSecret           : 1;
    uint16_t WriteKey           : 4;
    uint16_t WriteConfig        : 4;
} __attribute__((packed));

struct KeyConfig {
    uint16_t Private            : 1;
    uint16_t PubInfo            : 1;
    uint16_t KeyType            : 3;
    uint16_t Lockable           : 1;
    uint16_t ReqRandom          : 1;
    uint16_t ReqAuth            : 1;
    uint16_t AuthKey            : 4;
    uint16_t IntrusionDisable   : 1;
    uint16_t RFU                : 1;
    uint16_t X509Id             : 2;
} __attribute__((packed));


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


void pack_slot_config(struct SlotConfig config, uint8_t *config_zone) {
    // Is this right?
    config_zone[0] = (
        config.ReadKey << 4 |
        config.NoMac << 3 |
        config.LimitedUse << 2 |
        config.EncryptRead << 1 |
        config.IsSecret << 0
    );
    config_zone[1] = (
        config.WriteKey << 4 |
        config.WriteConfig << 0
    );
}


void pack_key_config(struct KeyConfig config, uint8_t *config_zone) {
    // Is this right?
    config_zone[0] = (
        config.Private << 7 |
        config.PubInfo << 6 |
        config.KeyType << 3 |
        config.Lockable << 2 |
        config.ReqRandom << 1 |
        config.ReqAuth << 0
    );
    config_zone[1] = (
        config.AuthKey << 4 |
        config.IntrusionDisable << 2 |
        config.RFU << 1 |
        config.X509Id << 0
    );
}


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
    uint8_t buf[128] = {0};
    
    assert_ATCA_SUCCESS(atcab_read_config_zone(&buf));
    struct SlotConfig slot_config = {
        .ReadKey = 0b1100,      // Bit 0 - sign arbitrary messages
                                // Bit 1 - sign internal messages
        .NoMac = 0,             // Bit 4 - Do not disable HMAC
        .LimitedUse = 0,        // Bit 5 - No usage limitations
        .EncryptRead = 0,       // Bit 6 - Cleartext read okay
        .IsSecret = 1,          // Bit 7 - Contents are secret
        .WriteKey = 0b0000,     // Bits 9-11 - Write using key 0
        .WriteConfig = 0b1110   // Bit 12 - Source key, parent
                                // Bit 13 - Clear text write off
                                // Bit 14 - Encryption on
                                // Bit 15 - Unset No authorising MAC needed
    };
    struct KeyConfig key_config = {
        .Private = 1,           // Bit 0 - Contains private key
        .PubInfo = 1,           // Bit 1 - Allow public key access
        .KeyType = 4,           // Bits 2 to 4 - P256 key
        .Lockable = 1,          // Bit 5 - Individual lockable
        .ReqRandom = 0,         // Bit 6 - No random nonce needed
        .ReqAuth = 0,           // Bit 7 - No prior auth needed
        .AuthKey = 0,           // Bits 8 to 11 - Use key 0 for auth
        .IntrusionDisable = 0,  // Bit 12 - Ignore intrusion latch
        .RFU = 0,               // Bit 13 - Fixed value
        .X509Id = 0             // Bits 14 and 15 - 0 as not a public key
    };
    
    // Patch this config into each of the 16 slots
    for (uint8_t i = 0; i < 16 ; i++) {
        pack_slot_config(slot_config, &buf[20 + 2*i]);
        pack_key_config(key_config, &buf[96 + 2*i]);
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

    for (int i=0;i<64;i++) {
        if (i%8 == 0) {
            printf("\n");
        }
        printf("%02x ", pubkey[i]);
    }
    printf("\n");
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(ecc108a_genkey_obj, ecc108a_genkey);



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
};
STATIC MP_DEFINE_CONST_DICT(ecc108a_module_globals, ecc108a_module_globals_table);

const mp_obj_module_t ecc108a_user_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&ecc108a_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_ecc108a, ecc108a_user_module, 1);
