# TiLDA mk6

This is a package containing a micropython board definition and additional driver modules for the EMF 2022 badge.

## Building using Docker

First, ensure you have a working Docker daemon on your machine. You'll need to build the docker image containing the SDK for the chip.

Then, you'll need to check out this repo and its submodules.

    git clone --recurse-submodules git@github.com:emfcamp/TiDAL-Firmware
    cd TiDAL-Firmware

If you forget the --recurse-submodules during the clone, then init post clone with:

    git submodule init
    git submodule update --recursive

Apply patches to submodules:

    ./scripts/firstTime.sh

Pull the docker image containing the IDF:

    docker pull matthewwilkes/esp_idf:4.4
    
This is (currently) very large. You can alternatively build this locally yourself:

    docker build . -t esp_idf:4.4

At this stage, you can run the image, mounting the current working directory as the firmware target:

    docker run -it -v "$(pwd)"/:/firmware matthewwilkes/esp_idf:4.4 IOT_SOLUTION_PATH=/firmware/esp-iot-solution TARGET=esp32s3

This will leave the firmware build context in `./micropython/ports/esp32/build-tildamk6` and output the flashing command. Only the three .bin files referenced are important.

However, if you have the device plugged into the machine running the docker container you can skip straight to a flash, just mount the device and add the deploy argument when running:

    docker run -it --device /dev/ttyUSB0 -v "$(pwd)"/:/firmware matthewwilkes/esp_idf:4.4 IOT_SOLUTION_PATH=/firmware/esp-iot-solution TARGET=esp32s3 deploy

### Prototypes

If you have one of the prototypes, you need to add an additional variable to the build command to ensure the right pin assignments are used. For the DEVKIT and PicoLCD breadboard prototype, wire up the Pico using the same pin assignments were possible and set:

    CONFIG_TIDAL_VARIANT_DEVBOARD=y

if you're using the electo magentic yield prototype, use:

    CONFIG_TIDAL_VARIANT_PROTOTYPE=y

If you need to switch which version you're building, run

    docker run -it "$(pwd)"/:/firmware matthewwilkes/esp_idf:4.4 IOT_SOLUTION_PATH=/firmware/esp-iot-solution TARGET=esp32s3 clean

to remove the cached definitions.

### Problems

You might need to force download mode on the board (by holding the Boot button down while booting/pressing Reset).

If your serial port is on a different name then map that with docker:

    docker run -it --device /dev/ttyACM0:/dev/ttyUSB0 -v "$(pwd)"/:/firmware matthewwilkes/esp_idf:4.4 IOT_SOLUTION_PATH=/firmware/esp-iot-solution TARGET=esp32s3 deploy

## Accessing the REPL

The ESP32S3 devboard offers the REPL on both the USB port and the UART port. You can use either (or both), and connect either or both cables. The REPL is on the ACM device at 115kbps (But see the lightsleep note in the Testing section below):

    screen /dev/ttyACM0 115200

## Adding drivers and configuration

The contents of the drivers directory are added as drivers into the firmware build. The board details are in tildamk6.

## Building on GitHub

GitHub pull requests will trigger a build that archives the firmware to artifacts.

## Testing

If you're using an ESP32S3 devboard you can connect to the USB serial console over the UART interface.

   screen /dev/ttyUSB0 115200

On one of our prototypes only ttyACM0 is available. REPL is not currently available on this port, due to incompatibility with the tinyUSB stack. _Not sure if this is still true..._

On boot, the device will boot into the blue Boot Menu and then immediately enter light sleep. This prevents any USB or UART debugging. To prevent this, hold down BUTTON_FRONT (or ground GPIO 6, on the devboard) during boot, to enter the Recovery Menu instead. This mode does not use light sleep. Once connected to the REPL over USB or the USB UART, you may have to press Ctrl-C to interrupt the running app.

The "Update Firmware" option in the boot menu is not yet kept up to date. For now, build and flash images yourself.