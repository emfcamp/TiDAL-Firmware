#include "descriptors_control.h"
#include "tidal_usb_u2f.h"
#include "u2f_hid.h"
#include "u2f.h"
#include "esp_log.h"
#include "u2f_crypto.h"
#include <unistd.h>
#include "py/builtin.h"

#include "tidal_usb_console.h"

#if CONFIG_TINYUSB_U2FHID_ENABLED
static const char *TAG = "tidalU2F";


uint8_t *in_progress_packet = NULL;
bool packet_needs_free = false;
uint16_t expected_size = 0;
uint16_t current_index = 0;

u2f_hid_msg upcoming_report_ring[REPORT_RING_SIZE] = { 0 };
bool upcoming_report_ring_waiting[REPORT_RING_SIZE] = { false };
uint8_t write_head = 0;
uint8_t read_head = 0;

void push_report(u2f_hid_msg *msg) {
    if (upcoming_report_ring_waiting[write_head]) {
        // There's already a report waiting to be picked up. This is a fatal error.
        ESP_LOGE(TAG, "U2F outbound report buffer full");
    }
    ESP_LOGI(TAG, "Writing into buffer at position %d", write_head);
    memcpy(&upcoming_report_ring[write_head], msg, sizeof(u2f_hid_msg));
    upcoming_report_ring_waiting[write_head] = true;
    write_head = (write_head + 1) % REPORT_RING_SIZE;
    return;
}

void pop_and_send_report() {
    if (!upcoming_report_ring_waiting[read_head]) {
        // There's no report waiting to be picked up. This is a fatal error.
        ESP_LOGW(TAG, "U2F outbound report buffer empty");
        return;
    }
    ESP_LOGI(TAG, "Sending pending report from position %d", read_head);
    u2f_report(&upcoming_report_ring[read_head]);
    upcoming_report_ring_waiting[read_head] = false;
    memset(&upcoming_report_ring[read_head], 0, sizeof(u2f_hid_msg));
    read_head = (read_head + 1) % REPORT_RING_SIZE;
}


bool handle_message_fragment(const uint8_t *buffer) {
    const u2f_hid_msg *msg = (u2f_hid_msg *) buffer;
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
        ESP_LOGI(TAG, "Got initial packet of size %d for message %x", msg_size, msg->init.CMD);

        if (msg_size <= HID_RPT_SIZE) {
            // No, it's small enough
            ESP_LOGI(TAG, "Using existing buffer");
            in_progress_packet = buffer;
            expected_size = msg_size;
            packet_needs_free = false;
            return true;
        } else {
            // This is the first fragment, set up a big enough buffer
            ESP_LOGI(TAG, "Allocating larger buffer");
            // The expected size is the reported data size plus the header on the initial packet
            expected_size = msg_size + 7;
            in_progress_packet = malloc(expected_size);
            // Copy the entire message, including the header
            uint16_t bytes_to_copy = HID_RPT_SIZE;
            memcpy(in_progress_packet, buffer, bytes_to_copy);
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

    ESP_LOGI(TAG, "Handling command %02x", msg->init.CMD);
    if (msg->init.CMD == U2FHID_INIT) {
        // INIT command
        handle_u2f_init((const u2fhid_init_request *) msg->init.data);
    } else if (msg->init.CMD == U2FHID_MSG) {
        handle_u2f_msg(msg->init.data, msg_size);
    } else if (msg->init.CMD == U2FHID_WINK) {
        handle_u2f_wink();
    } else {
        ESP_LOGE(TAG, "Unknown U2FHID transport command %02x", msg->init.CMD);
        // Unknown report type, log it.
        /*printf("REPORT: %d %d %d\n", itf, report_id, report_type);
        for (int i=0;i<expected_size;i++) {
            if (i%8 == 0) {
                printf("\n");
            }
            printf("%02x ", in_progress_packet[i]);
        }
        printf("\n");*/
        u2f_hid_msg response = {
            .CID = msg->CID,
            .init.CMD = U2FHID_ERROR,
            .init.BCNTH = 0,
            .init.BCNTL = 1,
            .init.data = { ERR_INVALID_CMD }
        };
        u2f_report(&response);
        
    }
    
    if (packet_needs_free) {
        ESP_LOGI(TAG, "Freeing temporary buffer");
        free(in_progress_packet);
        packet_needs_free = false;
    }
    in_progress_packet = NULL;
    expected_size = current_index = 0;

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
        .CAPABILITIES = 0 //CAPFLAG_WINK
    };
    
    // Allocate a response report
    u2f_hid_msg response = {
        .CID = CID_BROADCAST,
        .init.CMD = U2FHID_INIT,
        .init.BCNTH = 0,
        .init.BCNTL = 17,
    };
    memcpy(response.init.data, &response_data, 17);
    
    // Send the report
    u2f_report(&response);
}

arbitrary_size_container process_register_command(u2f_raw_register_request_body *register_params) {
    ESP_LOGI(TAG, "Allocating container");
    arbitrary_size_container response_data = {
        .size=0,
        .data=malloc(1024)
    };
    memset(response_data.data, 0x00, 1024);
    size_t write_head = 0;
    uint8_t handle = allocate_handle();
    uint8_t signature_input[131] = { 0 };


    // Set reserved byte
    ESP_LOGI(TAG, "Setting header");
    response_data.data[write_head++] = 0x05;

    // The next 65 bytes are the pubkey
    ESP_LOGI(TAG, "Setting pubkey");
    set_pubkey(handle, response_data.data + write_head);
    write_head += 65;

    // Then handle length followed by handle
    ESP_LOGI(TAG, "Setting handle");
    response_data.data[write_head++] = 0x01;
    response_data.data[write_head++] = handle;

    
    // Attestation certificate
    ESP_LOGI(TAG, "Setting cert");
    // Get the certificate from the secure element
    arbitrary_size_container cert = get_attestation_certificate();
    // Copy it into the current data stream
    memcpy(response_data.data + write_head, cert.data, cert.size);
    write_head += cert.size;
    // Free the intermediate copy
    free(cert.data);

    // Create the signature out of 0x00, the register request, key handle and pubkey
    ESP_LOGI(TAG, "Setting signature");
    signature_input[0] = 0x00;
    memcpy(signature_input + 1, register_params, 65);
    signature_input[66] = handle;
    memcpy(signature_input + 67, response_data.data + 1, 64);
    arbitrary_size_container signature;
    write_head += get_signature(1, 131, signature_input, response_data.data + write_head);

    // Set the status epilogue
    response_data.data[write_head++] = U2F_SW_NO_ERROR >> 8;
    response_data.data[write_head++] = U2F_SW_NO_ERROR &  0xFF;
    ESP_LOGI(TAG, "Built %d byte register response", write_head);
    response_data.size = write_head;
    //realloc(response_data.data, write_head);
    
    printf("RAW data:");
    for (int i=0;i<response_data.size;i++) {
        if (i%8 == 0) {
            printf("\n");
            printf("%04x : ", i);
        }
        printf("%02x ", response_data.data[i]);
    }
    printf("\n");
    /**/
    return response_data;
}


arbitrary_size_container process_authenticate_command(uint8_t control, u2f_raw_authenticate_request_body *authenticate_params) {
    if (control == 7) {
        ESP_LOGI(TAG, "Allocating container");
        // Valid responses from this are test of presence required or bad key handle.
        arbitrary_size_container response_data = {
            .size=2,
            .data=malloc(2)
        };
        // Set valid response
        response_data.data[0] = U2F_SW_CONDITIONS_NOT_SATISFIED >> 8;
        response_data.data[1] = U2F_SW_CONDITIONS_NOT_SATISFIED &  0xFF;
        return response_data;
    }

    ESP_LOGI(TAG, "Allocating container");
    arbitrary_size_container response_data = {
        .size=0,
        .data=malloc(185)
    };
    memset(response_data.data, 0x00, 185);
    size_t write_head = 0;

    // Set reserved byte
    ESP_LOGI(TAG, "Setting presence bit");
    response_data.data[write_head++] = 0x01;
    // The next 4 bytes are a counter, increment it for this handle and return
    uint32_t counter_value = 1;
    set_counter(authenticate_params->key_handle[0], &counter_value);
    response_data.data[write_head++] = 0x00;//(counter_value >> 24) && 0xFF;
    response_data.data[write_head++] = 0x00;//(counter_value >> 16) && 0xFF;
    response_data.data[write_head++] = 0x00;//(counter_value >>  8) && 0xFF;
    response_data.data[write_head++] = 0x00;//(counter_value >>  0) && 0xFF;
    
    // Create the signature out of the application parameter, the user presence byte, the counter then the challenge param
    ESP_LOGI(TAG, "Setting signature");
    uint8_t signature_input[69] = { 0 };
    memcpy(signature_input +  0, authenticate_params->application_param, 32);
    memcpy(signature_input + 32, response_data.data, 5);
    memcpy(signature_input + 37, authenticate_params->challenge_param, 32);
    write_head += get_signature(authenticate_params->key_handle[0], 69, signature_input, response_data.data + write_head);

    // Set the status epilogue
    response_data.data[write_head++] = U2F_SW_NO_ERROR >> 8;
    response_data.data[write_head++] = U2F_SW_NO_ERROR &  0xFF;
    ESP_LOGI(TAG, "Built %d byte authenticate response", write_head);
    response_data.size = write_head;
    //realloc(response_data.data, write_head);

    
    /*printf("RAW data:");
    for (int i=0;i<response_data.size;i++) {
        if (i%8 == 0) {
            printf("\n");
            printf("%04x : ", i);
        }
        printf("%02x ", response_data.data[i]);
    }
    printf("\n");
*/
    return response_data;
}

void send_multipart_response(arbitrary_size_container *response_data) {
    ESP_LOGI(TAG, "Sending multipart message of length %d", response_data->size);
    uint16_t place = 0;
    uint8_t seq = 0;
    u2f_hid_msg response = {
        .CID = TIDAL_CHANNEL,
        .init.CMD = U2FHID_MSG,
        .init.BCNTH = (response_data->size >>   8),
        .init.BCNTL = (response_data->size & 0xFF),
        .init.data = { 0 }
    };
    memcpy(response.init.data, response_data->data + place, sizeof(response.init.data));
    ESP_LOGI(TAG, "Sending initial packet %d/%d", place, response_data->size);
    place += sizeof(response.init.data);
    while (place < response_data->size) {
        u2f_hid_msg next_report = {
            .CID = TIDAL_CHANNEL,
            .cont.SEQ = seq++,
            .cont.data = { 0 }
        };
        memcpy(next_report.cont.data, response_data->data + place, sizeof(next_report.cont.data));
        ESP_LOGI(TAG, "Sending continuation packet %d/%d", place, response_data->size);
        place += sizeof(next_report.cont.data);
        push_report(&next_report);
    }
    u2f_report(&response);
}

void handle_u2f_msg(uint8_t *buffer, uint16_t bufsize) {
    
    /*printf("U2FMSG:");
    for (int i=0;i<bufsize;i++) {
        if (i%8 == 0) {
            printf("\n");
        }
        printf("%02x ", buffer[i]);
    }
    printf("\n");
    */
    u2f_raw_request_msg *raw_message = (u2f_raw_request_msg *) buffer;
    
    if (raw_message->INS == U2F_REGISTER) {
        ESP_LOGI(TAG, "Will process U2F_REGISTER raw message (Instruction %x)", raw_message->INS);
        u2f_raw_register_request_body *register_params = (u2f_raw_register_request_body *) raw_message->extended_form.data;
        
        if (authentication_operation == NO_OPERATION || authentication_operation == REGISTER_REQUEST) {
            // Set shared variables with micropython
            authentication_operation = REGISTER_REQUEST;
            memcpy(authentication_application_parameter, register_params->application_param, 32);

            // The user needs to allow this, send back the conditions
            // not satisfied status as the only body
            ESP_LOGI(TAG, "Awaiting user interaction, reporting conditions not satisfied");
            u2f_hid_msg response = {
                .CID = TIDAL_CHANNEL,
                .init.CMD = U2FHID_MSG,
                .init.BCNTH = 0,
                .init.BCNTL = 0x02,
                .init.data = {
                    (U2F_SW_CONDITIONS_NOT_SATISFIED >> 8),
                    (U2F_SW_CONDITIONS_NOT_SATISFIED & 0xff)
                }
            };
            u2f_report(&response);
        } else if (authentication_operation == REGISTER_APPROVED) {
            // Reset the interaction flag
            arbitrary_size_container response_data = process_register_command(register_params);
            send_multipart_response(&response_data);
            authentication_operation = NO_OPERATION;
            authentication_operation_slot = 99;
            free(response_data.data);
        }
    } else if (raw_message->INS == U2F_AUTHENTICATE) {

/*        arbitrary_size_container response_data = {
        .size=185,
        .data=malloc(185)
    };
    size_t write_head = 0;

    memcpy(response_data.data, raw_message->extended_form.data, 70);
    response_data.size = 70;
    realloc(response_data.data, 70);
  */  
    
        ESP_LOGI(TAG, "Will process U2F_AUTHENTICATE raw message (Instruction %x)", raw_message->INS);
        u2f_raw_authenticate_request_body *authenticate_params = (u2f_raw_authenticate_request_body *) raw_message->extended_form.data;

        if (authentication_operation == KEY_MISMATCH) {
            u2f_hid_msg response = {
                .CID = TIDAL_CHANNEL,
                .init.CMD = U2FHID_MSG,
                .init.BCNTH = 0,
                .init.BCNTL = 0x02,
                .init.data = {
                    (U2F_SW_WRONG_DATA >> 8),
                    (U2F_SW_WRONG_DATA & 0xff)
                }
            };
            u2f_report(&response);
            authentication_operation = NO_OPERATION;
        } else if (authentication_operation == AUTHENTICATE_APPROVED) {
            arbitrary_size_container response_data = process_authenticate_command(raw_message->P1, authenticate_params);
            send_multipart_response(&response_data);
            free(response_data.data);
            authentication_operation = NO_OPERATION;
            authentication_operation_slot = 99;
        }
        else {
            // The user needs to allow this, send back the conditions
            // not satisfied status as the only body

            // Set shared variables with micropython
            authentication_operation = AUTHENTICATE_REQUEST;
            authentication_operation_slot = authenticate_params->key_handle[0];
            memcpy(authentication_application_parameter, authenticate_params->application_param, 32);

            ESP_LOGI(TAG, "Awaiting user interaction, reporting conditions not satisfied");
            u2f_hid_msg response = {
                .CID = TIDAL_CHANNEL,
                .init.CMD = U2FHID_MSG,
                .init.BCNTH = 0,
                .init.BCNTL = 0x02,
                .init.data = {
                    (U2F_SW_CONDITIONS_NOT_SATISFIED >> 8),
                    (U2F_SW_CONDITIONS_NOT_SATISFIED & 0xff)
                }
            };
            u2f_report(&response);
        } 
    }  else {
        ESP_LOGE(TAG, "Got U2F raw message, but instruction %x is not known", raw_message->INS);
    }
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
    // For some reason, sending with a report ID of 0 is causing
    // timeout then -ENOENT, so as long as the 0th byte of the
    // buffer isn't a 0 we can do a really filthy hack and put that
    // in the report id field.
    // Sit Deus propitius huic potatori

    uint8_t *as_buf = (uint8_t *) cmd;
    /*printf("Sending response packet");
    for (int i=0;i<HID_RPT_SIZE;i++) {
        printf("%x ", as_buf[i]);
    }
    printf("\n");
    */

    tud_hid_report(as_buf[0], as_buf+1, HID_RPT_SIZE-1);
}
#endif