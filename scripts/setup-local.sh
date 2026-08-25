# This script setups the build environment for the project when used outside of the docker container.
# This has been tested on a native Ubuntu 20.04 LTS only, I am not sure if it will work on other platforms.
# It should be executed from the project root directory.

sudo apt-get update
sudo apt-get install -y software-properties-common
sudo apt-get update
sudo add-apt-repository ppa:git-core/ppa
sudo apt-get update
sudo apt-get install -y build-essential python3-pip libusb-1.0-0-dev cmake wget zip git python3-pillow

# Download the ESP-IDF v4.4 release and install it
# Do this all in one step to avoid creating extraneous layers
mkdir ./esp-idf && git clone -b v4.4 --recurse-submodules https://github.com/espressif/esp-idf /esp-idf && ./esp-idf/install.sh
