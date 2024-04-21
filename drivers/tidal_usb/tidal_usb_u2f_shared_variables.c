#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include "tidal_usb_u2f_shared_variables.h"

enum authentication_state authentication_operation = NO_OPERATION;
uint8_t authentication_operation_slot = 99;
uint8_t authentication_application_parameter[32] = { 0 };
size_t authentication_length_to_sign = 0;
uint8_t authentication_value_to_sign[256] = { 0 };
uint8_t authentication_signature[64] = { 0 };