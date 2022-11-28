#include <stddef.h>
#include <stdint.h>

typedef struct arbitrary_size_container {
    size_t size;
    uint8_t *data;
} arbitrary_size_container;

arbitrary_size_container get_attestation_certificate();
size_t get_signature(uint8_t handle, uint8_t *signature_input, uint8_t *target);
void set_counter(uint8_t handle, uint32_t *target);
void set_pubkey(uint8_t handle, uint8_t *target);
uint8_t allocate_handle();
size_t der_encode_signature(uint8_t *signature, uint8_t *target);