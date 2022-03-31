# TiLDA mk6

This is a package containing a micropython board definition and additional driver modules for the EMF 2022 badge.

## Building using Docker

First, ensure you have a working Docker daemon on your machine. You'll need to build the docker image containing the SDK for the chip.

TODO: Can we pre-build this and distribute this, given the licence?

Then, you'll need to check out this repo and its submodules.

    git clone --recurse-submodules git@github.com:emfcamp/Mk6-micropython-board
    cd Mk6-micropython-board
    docker build . -t esp_idf:4.4

*Note:* There are currently some patcdirhes required to fix USB:

    cd micropython
    git apply ../micropython.diff
    cd ../esp-iot-solution
    git apply ../esp-iot-solution.diff
    cd ..

At this stage, you can run the image, mounting the current working directory as the firmware targer

    docker run -it -v "$(pwd)"/:/firmware esp_idf:4.4 IOT_SOLUTION_PATH=/firmware/esp-iot-solution TARGET=esp32s3

This will leave the firmware build context in `./micropython/ports/esp32/build-tildamk6` and output the flashing command. Only the three .bin files referenced are important.

However, if you have the device plugged into the machine running the docker container you can skip straight to a flash, just mount the device and add the deploy argument when running:

    docker run -it --device /dev/ttyUSB0 -v "$(pwd)"/:/firmware esp_idf:4.4 IOT_SOLUTION_PATH=/firmware/esp-iot-solution TARGET=esp32s3 deploy


### Problems

You might need to force download mode on the board. If your serial port is on a different name then map that with docker:

    docker run -it --device /dev/ttyACM0:/dev/ttyUSB0 -v "$(pwd)"/:/firmware upydrivers IOT_SOLUTION_PATH=/firmware/esp-iot-solution TARGET=esp32s3 deploy

## Accessing the REPL

The ESP32S3 devboard offers the REPL on the USB port, not the UART port. You need to plug both in. The REPL is on the ACM device at 115kbps.

    screen /dev/ttyACM0 115200

## Adding drivers and configuration

The contents of the drivers directory are added as drivers into the firmware build. The board details are in tildamk6.

## Building on GitHub

GitHub pull requests will trigger a build that archives the firmware to artifacts. You can test the action using act. Install using: https://github.com/nektos/act

Then run:

    act

No artifacts will be archived locally, so you can't actually install the compiled firmware through this method.


## Testing

Connect to the USB serial console:

   screen /dev/ttyUSB0 115200

It may be ACM0, it may be something else. You may need to reboot to get a REPL.

Sending a keyboard key:

    MicroPython v1.18-228-gafceb56ee-dirty on 2022-03-31; TiLDA mk6 with ESP32S3
    Type "help()" for more information.
    >>> import tilda_hid
    >>> tilda_hid.set_usb_mode()
    >>> tilda_hid.send_key(2)
    Guru Meditation Error: Core  1 panic'ed (LoadProhibited). Exception was unhandled.

    Core  1 register dump:
    PC      : 0x4200809d  PS      : 0x00060d30  A0      : 0x82002068  A1      : 0x3fce4980  
    A2      : 0x00000002  A3      : 0x00000000  A4      : 0x00000001  A5      : 0x3d82f510  
    A6      : 0x3d82f460  A7      : 0x000000fa  A8      : 0x8200809b  A9      : 0x3fce4960  
    A10     : 0x00000001  A11     : 0x00000000  A12     : 0x00000000  A13     : 0x00000000  
    A14     : 0x0000003f  A15     : 0x00000005  SAR     : 0x0000001a  EXCCAUSE: 0x0000001c  
    EXCVADDR: 0x00000002  LBEG    : 0x400570e8  LEND    : 0x400570f3  LCOUNT  : 0x00000000  


    Backtrace:0x4200809a:0x3fce49800x42002065:0x3fce49b0 0x4200b79d:0x3fce49f0 0x42011d19:0x3fce4a10 0x42011e2d:0x3fce4a30 0x403783b5:0x3fce4a50 0x4200b8b0:0x3fce4af0 0x42011d19:0x3fce4b50 0x42011d42:0x3fce4b70 0x4203da16:0x3fce4b90 0x4203dd48:0x3fce4c20 0x420210cc:0x3fce4c60 


Moving the mouse:

    MicroPython v1.18-228-gafceb56ee-dirty on 2022-03-31; TiLDA mk6 with ESP32S3
    Type "help()" for more information.
    >>> 
    >>> import tilda_hid
    >>> tilda_hid.set_usb_mode()
    >>> tilda_hid.move_mouse(100,100)

