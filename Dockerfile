# Start with vaguely modernish ubuntu that doesn't have seccomp compat issues
FROM ubuntu:20.04

# Prevent tzinfo prompts
ARG DEBIAN_FRONTEND=noninteractive

# Update apt and install build dependencies
RUN apt-get update && apt-get install -y build-essential python3-pip libusb-1.0-0-dev cmake wget zip git
RUN python3 -m pip install pillow

# Download the ESP-IDF v4.4 release
RUN mkdir /esp-idf
WORKDIR /esp-idf
RUN git clone -b v4.4 --recurse-submodules https://github.com/espressif/esp-idf /esp-idf

# Install the IDF, triggering the xtensa install
WORKDIR /esp-idf
RUN ./install.sh

# Copy the build script in and define that as the entrypoint
COPY scripts/build.sh /
ENTRYPOINT ["/build.sh"]