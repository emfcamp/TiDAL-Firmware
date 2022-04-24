#include "descriptors_control.h"
#include "tidal_usb_u2f.h"
#include "u2f_hid.h"

void handle_report_u2f(uint8_t itf, uint8_t report_id, hid_report_type_t report_type, uint8_t const* buffer, uint16_t bufsize) { 
    const u2f_hid_msg *msg = buffer;

    if (msg->init.CMD == U2FHID_INIT) {
        // INIT command
        handle_u2f_init(&buffer[7]);
    }// else {
        // Unknown report type, log it.
        printf("REPORT: %d %d %d\n", itf, report_id, report_type);
        for (int i=0;i<bufsize;i++) {
            printf("%x ", buffer[i]);
        }
        printf("\n");
    //}

}
 
void handle_u2f_init(u2fhid_init_request const* init_request) {
    // Receives an 8-byte n-once
    printf("U2FHID_INIT: nonce = %llx\n", init_request->NONCE);

    printf("Responding...\n");
    // Allocate a response object for the init request's response
    u2fhid_init_response response_data;
    response_data.NONCE = init_request->NONCE;
    response_data.CID = CID_BROADCAST;
    response_data.PROTOCOL_VER = 0x01;
    response_data.DEVICE_VER_MAJOR = 0x01;
    response_data.DEVICE_VER_MINOR = 0x01;
    response_data.DEVICE_VER_BUILD = 0x01;
    response_data.CAPABILITIES = CAPFLAG_WINK;
    
    printf("U2FHID_INIT: response nonce = %llx\n", response_data.NONCE);

    
    // Allocate a response report
    u2f_hid_msg response;
    // Set the same CMD and CID as the input
    response.CID = CID_BROADCAST;
    response.init.CMD = U2FHID_INIT;
    // Zero out the data packet and then copy in the (17 byte)
    // response and set the length flags.
    memset(response.init.data, 0, sizeof response.init.data);
    memcpy(response.init.data, &response_data, 17);
    response.init.BCNTH = 0;
    response.init.BCNTL = 17;
    
    // Cast this to a char array so we can debug print it
    uint8_t *as_buf = (uint8_t *) &response;
    for (int i=0;i<64;i++) {
        printf("%x ", as_buf[i]);
    }
    printf("\n");

    // Send the report
    u2f_report(&response);
}

void u2f_report(u2f_hid_msg *cmd) {
    // This is wrong, but I'm just trying to make it match
    // what a real one is doing for now, to help debug.
    uint8_t *as_buf = (uint8_t *) cmd;
    tud_hid_n_report(0, as_buf[0], as_buf + 1, HID_RPT_SIZE-1);
}