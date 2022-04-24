#import "u2f_hid.h"

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
void u2f_report(u2f_hid_msg *cmd);