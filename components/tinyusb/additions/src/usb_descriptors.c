// Copyright 2020 Espressif Systems (Shanghai) PTE LTD
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "usb_descriptors.h"
#include "descriptors_control.h"
#include "sdkconfig.h"

/* A combination of interfaces must have a unique product id, since PC will save device driver after the first plug.
 * Same VID/PID with different interface e.g MSC (first), then CDC (later) will possibly cause system error on PC.
 *
 * Auto ProductID layout's Bitmap:
 *   [MSB]       NET | VENDOR | MIDI | HID | MSC | CDC          [LSB]
 */
#define USB_TUSB_PID (0x4000 | _PID_MAP(CDC, 0) | _PID_MAP(MSC, 1) | _PID_MAP(HID, 2) | \
                     _PID_MAP(MIDI, 3) | _PID_MAP(VENDOR, 4) | _PID_MAP(NET, 5) )

/**** TinyUSB default ****/
tusb_desc_device_t descriptor_tinyusb = {
    .bLength = sizeof(descriptor_tinyusb),
    .bDescriptorType = TUSB_DESC_DEVICE,
    .bcdUSB = 0x0200,

#if CFG_TUD_CDC
    // Use Interface Association Descriptor (IAD) for CDC
    // As required by USB Specs IAD's subclass must be common class (2) and protocol must be IAD (1)
    .bDeviceClass = TUSB_CLASS_MISC,
    .bDeviceSubClass = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol = MISC_PROTOCOL_IAD,
#else
    .bDeviceClass = 0x00,
    .bDeviceSubClass = 0x00,
    .bDeviceProtocol = 0x00,
#endif

    .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,

    .idVendor = 0xCafe,
    .idProduct = USB_TUSB_PID,
    .bcdDevice = 0x0100,

    .iManufacturer = 0x01,
    .iProduct = 0x02,
    .iSerialNumber = 0x03,

    .bNumConfigurations = 0x01
};

tusb_desc_strarray_device_t descriptor_str_tinyusb = {
    // array of pointer to string descriptors
    (char[]){0x09, 0x04}, // 0: is supported language is English (0x0409)
    "TinyUSB",            // 1: Manufacturer
    "TinyUSB Device",     // 2: Product
    "123456",             // 3: Serials, should use chip ID
    "TinyUSB CDC",        // 4: CDC Interface
    "TinyUSB MSC",        // 5: MSC Interface
    "TinyUSB HID"         // 6: HID
};
/* End of TinyUSB default */

/**** Kconfig driven Descriptor ****/
tusb_desc_device_t descriptor_kconfig = {
    .bLength = sizeof(descriptor_kconfig),
    .bDescriptorType = TUSB_DESC_DEVICE,
    .bcdUSB = 0x0200,

#if CFG_TUD_CDC
    // Use Interface Association Descriptor (IAD) for CDC
    // As required by USB Specs IAD's subclass must be common class (2) and protocol must be IAD (1)
    .bDeviceClass = TUSB_CLASS_MISC,
    .bDeviceSubClass = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol = MISC_PROTOCOL_IAD,
#elif CFG_TUD_BTH
    .bDeviceClass = TUSB_CLASS_WIRELESS_CONTROLLER,
    .bDeviceSubClass = TUD_BT_APP_SUBCLASS,
    .bDeviceProtocol = TUD_BT_PROTOCOL_PRIMARY_CONTROLLER,
#else
    .bDeviceClass = 0x00,
    .bDeviceSubClass = 0x00,
    .bDeviceProtocol = 0x00,
#endif

    .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,

#if CONFIG_TINYUSB_DESC_USE_ESPRESSIF_VID
    .idVendor = USB_ESPRESSIF_VID,
#else
    .idVendor = CONFIG_TINYUSB_DESC_CUSTOM_VID,
#endif

#if CONFIG_TINYUSB_DESC_USE_DEFAULT_PID
    .idProduct = USB_TUSB_PID,
#else
    .idProduct = CONFIG_TINYUSB_DESC_CUSTOM_PID,
#endif

    .bcdDevice = CONFIG_TINYUSB_DESC_BCD_DEVICE,

    .iManufacturer = 0x01,
    .iProduct = 0x02,
    .iSerialNumber = 0x03,

    .bNumConfigurations = 0x01
};

tusb_desc_strarray_device_t descriptor_str_kconfig = {
    // array of pointer to string descriptors
    (char[]){0x09, 0x04},                    // 0: is supported language is English (0x0409)
    CONFIG_TINYUSB_DESC_MANUFACTURER_STRING, // 1: Manufacturer
    CONFIG_TINYUSB_DESC_PRODUCT_STRING,      // 2: Product
    CONFIG_TINYUSB_DESC_SERIAL_STRING,       // 3: Serials, should use chip ID

#if CFG_TUD_CDC
    CONFIG_TINYUSB_DESC_CDC_STRING,          // CDC Interface
#endif

#if CFG_TUD_NET
    CONFIG_TINYUSB_DESC_NET_STRING,          // NET Interface
    "",                                      // MAC
#endif

#if CFG_TUD_MSC
    CONFIG_TINYUSB_DESC_MSC_STRING,          // MSC Interface
#endif

#if CFG_TUD_HID_KBD
    CONFIG_TINYUSB_DESC_HID_STRING,           // HIDs
#endif
#if CFG_TUD_U2FHID
    "TiDAL U2F",                              // U2FHID
#endif

#if CFG_TUD_BTH
    CONFIG_TINYUSB_DESC_BTH_STRING,          // BTH
#endif

#if CFG_TUD_DFU
    "FLASH",                       // 4: DFU Partition 1
    "EEPROM",                      // 5: DFU Partition 2
#endif

};
/* End of Kconfig driven Descriptor */
