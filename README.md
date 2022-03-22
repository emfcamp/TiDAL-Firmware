# TiLDA mk6

This is a package containing a micropython board definition and additional driver modules for the EMF 2022 badge.

## Building using Docker

First, ensure you have a working Docker daemon on your machine. You'll need to build the docker image containing the SDK for the chip.

TODO: Can we pre-build this and distribute this, given the licence?

Then, you'll need to check out this repo and its submodules.

    git clone --recurse-submodules git@github.com:emfcamp/Mk6-micropython-board
    docker build . -t esp_idf:4.4

At this stage, you can run the image, mounting the current working directory as the firmware targer

    docker run -it -v "$(pwd)"/:/firmware esp_idf:4.4 

This will leave the firmware build context in `./micropython/ports/esp32/build-tildamk6` and output the flashing command. Only the three .bin files referenced are important.

However, if you have the device plugged into the machine running the docker container you can skip straight to a flash, just mount the device and add the deploy argument when running:

    docker run -it --device /dev/ttyUSB0 -v "$(pwd)"/:/firmware esp_idf:4.4 deploy

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
