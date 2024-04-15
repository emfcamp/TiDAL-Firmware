#include <stdint.h>
#include <stdbool.h>

enum authentication_state {
    NO_OPERATION,
    REGISTER_REQUEST,
    REGISTER_APPROVED,
    AUTHENTICATE_REQUEST,
    AUTHENTICATE_APPROVED,
    USER_REFUSED,
    KEY_MISMATCH,
};
enum authentication_state authentication_operation;
uint8_t authentication_operation_slot;
uint8_t authentication_application_parameter[32];
