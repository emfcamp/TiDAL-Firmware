#include "u2f_hid.h"

#define min(a, b) (((a) < (b)) ? (a) : (b))

#define TIDAL_CHANNEL 0x81811818 //1 - ask the bill payer's permission

// U2F Raw support
#define MAX_SHORT_RAW_DATA_LENGTH 255
#define MAX_EXTENDED_RAW_DATA_LENGTH 65535
typedef struct u2f_raw_request_msg {
    uint8_t CLA;
    uint8_t INS;
    uint8_t P1;
    uint8_t P2;
    union {
        struct {
            uint8_t LC;
            uint8_t data[MAX_SHORT_RAW_DATA_LENGTH];
        } short_form;
        struct {
            uint8_t LCH;
            uint8_t LCM;
            uint8_t LCL;
            uint8_t data[MAX_EXTENDED_RAW_DATA_LENGTH];
        } extended_form;
        struct {
            
        } no_body;
    };
} __packed u2f_raw_request_msg;

typedef struct u2f_raw_register_request_body {
    uint8_t challenge_param[32];
    uint8_t application_param[32];
} __packed u2f_raw_register_request_body;

typedef struct u2f_raw_authenticate_request_body {
    uint8_t challenge_param[32];
    uint8_t application_param[32];
    uint8_t key_handle_length;
    uint8_t key_handle[];
} __packed u2f_raw_authenticate_request_body;


// U2F HIF support

#define REPORT_RING_SIZE 16

typedef struct u2f_hid_msg {
    uint32_t CID;
    union {
        struct {
            uint8_t CMD;
            uint8_t BCNTH;
            uint8_t BCNTL;
            uint8_t data[HID_RPT_SIZE - 7];
        } init;
        struct {
            uint8_t SEQ;
            uint8_t data[HID_RPT_SIZE - 5];
        } cont;
    };
} __packed u2f_hid_msg;


typedef struct u2fhid_init_request {
    uint64_t NONCE;
    uint8_t padding[HID_RPT_SIZE - 15];
} __packed u2fhid_init_request;

typedef struct u2fhid_init_response {
    uint64_t NONCE;
    uint32_t CID;
    uint8_t PROTOCOL_VER;
    uint8_t DEVICE_VER_MAJOR;
    uint8_t DEVICE_VER_MINOR;
    uint8_t DEVICE_VER_BUILD;
    uint8_t CAPABILITIES;
} __packed u2fhid_init_response;


void handle_report_u2f(uint8_t itf, uint8_t report_id, hid_report_type_t report_type, uint8_t const* buffer, uint16_t bufsize);

void handle_u2f_init(u2fhid_init_request const* init_request);
void handle_u2f_msg(uint8_t *buffer, uint16_t bufsize);
void handle_u2f_wink();
void u2f_report(u2f_hid_msg *cmd);

void push_report(u2f_hid_msg *msg);
void pop_and_send_report();
