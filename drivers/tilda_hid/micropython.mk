TILDA_HID_MOD_DIR := $(USERMOD_DIR)

# Add all C files to SRC_USERMOD.
SRC_USERMOD += $(TILDA_HID_MOD_DIR)/tilda_hids.c

# We can add our module folder to include paths if needed
# This is not actually needed in this example.
CFLAGS_USERMOD += -I$(TILDA_HID_MOD_DIR)
CEXAMPLE_MOD_DIR := $(USERMOD_DIR)
