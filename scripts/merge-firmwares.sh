#!/bin/bash
set -e -o pipefail

source ~/.profile

#. /opt/esp/entrypoint.sh
source /esp-idf/export.sh
cd /firmware/micropython/ports/esp32
python /esp-idf/components/esptool_py/esptool/esptool.py --chip esp32s3 -b 460800 merge_bin -o /firmware/flasher/merged-firmware.bin --flash_mode dio --flash_freq 80m --flash_size 8MB 0x0 build-tildamk6/bootloader/bootloader.bin 0x10000 build-tildamk6/micropython.bin 0x8000 build-tildamk6/partition_table/partition-table.bin 0xd000 build-tildamk6/ota_data_initial.bin