#include "py/mphal.h"

#define ATCA_ATECC108A_SUPPORT
#define ATCA_POST_DELAY_MSEC 25
#define ATCA_HAL_I2C

#define ATCA_PLATFORM_MALLOC malloc
#define ATCA_PLATFORM_FREE free

#define ATCA_TIDAL

#define atca_delay_ms   mp_hal_delay_ms
#define atca_delay_us   mp_hal_delay_us

