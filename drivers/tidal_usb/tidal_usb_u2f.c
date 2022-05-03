#include "descriptors_control.h"
#include "tidal_usb_u2f.h"
#include "u2f_hid.h"
#include "esp_log.h"

#ifdef CFG_TUD_U2FHID
static const char *TAG = "tidalU2F";


uint8_t *in_progress_packet = NULL;
bool packet_needs_free = false;
uint16_t expected_size = NULL;
uint16_t current_index = NULL;

bool handle_message_fragment(uint8_t *buffer) {
    const u2f_hid_msg *msg = buffer;
    if (in_progress_packet != NULL) {
        // This is a continuation packet
        uint16_t bytes_to_copy = min(sizeof(msg->cont.data), expected_size-current_index);
        ESP_LOGI(TAG, "Got continuation packet, will copy %d bytes", bytes_to_copy);
        // Copy the next section in, only from the data
        memcpy(in_progress_packet + current_index, msg->cont.data, bytes_to_copy);
        current_index += bytes_to_copy;
        if (current_index >= expected_size) {
            ESP_LOGI(TAG, "Finished receiving packet");
            return true;
        } else {
            return false;
        }
    } else {
        // This is a command packet, check if we need to set
        // up a continuation
        uint16_t msg_size = (msg->init.BCNTH << 8) + msg->init.BCNTL;
        ESP_LOGI(TAG, "Got message of size %d", msg_size);

        if (msg_size <= HID_RPT_SIZE) {
            // No, it's small enough
            ESP_LOGI(TAG, "Using existing buffer");
            in_progress_packet = msg;
            expected_size = msg_size;
            packet_needs_free = false;
            return true;
        } else {
            // This is the first fragment, set up a big enough buffer
            ESP_LOGI(TAG, "Allocating larger buffer");
            in_progress_packet = malloc(msg_size);
            expected_size = msg_size;
            // Copy the entire message, including the header
            uint16_t bytes_to_copy = HID_RPT_SIZE;
            memcpy(in_progress_packet + current_index, buffer, bytes_to_copy);
            current_index = bytes_to_copy;
            packet_needs_free = true;
            return false;
        } 
    }
}


void handle_report_u2f(uint8_t itf, uint8_t report_id, hid_report_type_t report_type, uint8_t const* buffer, uint16_t bufsize) { 
    if (!handle_message_fragment(buffer)) {
        return;
    }
    
    const u2f_hid_msg *msg = in_progress_packet;
    uint16_t msg_size = (msg->init.BCNTH << 8) + msg->init.BCNTL;

    ESP_LOGI(TAG, "Handling command %02x (%d)", msg->init.CMD, msg->init.CMD);
    if (msg->init.CMD == U2FHID_INIT) {
        // INIT command
        handle_u2f_init((const u2fhid_init_request *) msg->init.data);
    } else if (msg->init.CMD == U2FHID_MSG) {
        handle_u2f_msg(msg->init.data, msg_size);
    } else if (msg->init.CMD == U2FHID_WINK) {
        handle_u2f_wink();
    } else {
        // Unknown report type, log it.
        printf("REPORT: %d %d %d\n", itf, report_id, report_type);
        for (int i=0;i<expected_size;i++) {
            if (i%8 == 0) {
                printf("\n");
            }
            printf("%02x ", in_progress_packet[i]);
        }
        printf("\n");
    }
    
    if (packet_needs_free) {
        ESP_LOGI(TAG, "Freeing temporary buffer");
        free(in_progress_packet);
        packet_needs_free = false;
    }
    in_progress_packet = expected_size = current_index = NULL;

}
 
void handle_u2f_init(u2fhid_init_request const* init_request) {
    // Receives an 8-byte n-once
    ESP_LOGI(TAG, "U2FHID_INIT: nonce = %llx", init_request->NONCE);

    ESP_LOGI(TAG, "Responding...");
    // Allocate a response object for the init request's response
    u2fhid_init_response response_data = {
        .NONCE = init_request->NONCE,
        .CID = TIDAL_CHANNEL,
        .PROTOCOL_VER = U2FHID_IF_VERSION,
        .DEVICE_VER_MAJOR = 0x03,
        .DEVICE_VER_MINOR = 0x04,
        .DEVICE_VER_BUILD = 0x05,
        .CAPABILITIES = CAPFLAG_WINK
    };
    
    // Allocate a response report
    u2f_hid_msg response = {
        .CID = CID_BROADCAST,
        .init.CMD = U2FHID_INIT,
        .init.BCNTH = 0,
        .init.BCNTL = 17,
    };
    // Zero out the data packet and then copy in the (17 byte)
    // response and set the length flags.
    memset(response.init.data, 0, sizeof response.init.data);
    memcpy(response.init.data, &response_data, 17);
    
    // Cast this to a char array so we can debug print it
    uint8_t *as_buf = (uint8_t *) &response;
    for (int i=0;i<64;i++) {
        printf("%x ", as_buf[i]);
    }
    printf("\n");

    // Send the report
    u2f_report(&response);
}

void handle_u2f_msg(uint8_t *buffer, uint16_t bufsize) {
    ESP_LOGE(TAG, "Not implemented");
    
    printf("U2FMSG:");
    for (int i=0;i<bufsize;i++) {
        if (i%8 == 0) {
            printf("\n");
        }
        printf("%02x ", buffer[i]);
    }
    printf("\n");
    
    u2f_hid_msg response = {
        .CID = TIDAL_CHANNEL,
        .init.CMD = U2FHID_MSG,
        .init.BCNTH = 0,
        .init.BCNTL = 0,
        .init.data = ""
    };
    u2f_report(&response);
}

void handle_u2f_wink() {
    ESP_LOGW(TAG, "WINKING!");

    u2f_hid_msg response = {
        .CID = TIDAL_CHANNEL,
        .init.CMD = U2FHID_WINK,
        .init.BCNTH = 0,
        .init.BCNTL = 0,
        .init.data = ""
    };
    u2f_report(&response);
}
void u2f_report(u2f_hid_msg *cmd) {
    // This is wrong, but I'm just trying to make it match
    // what a real one is doing for now, to help debug.
    uint8_t *as_buf = (uint8_t *) cmd;
    //tud_hid_n_report(ITF_NUM_HID_2, 0, as_buf, HID_RPT_SIZE-1);
}
#endif