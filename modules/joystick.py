from tilda_hid import set_usb_mode, send_key
from machine import Pin


HID_KEY_A                         = 0x04
HID_KEY_B                         = 0x05
HID_KEY_ARROW_RIGHT               = 0x4F
HID_KEY_ARROW_LEFT                = 0x50
HID_KEY_ARROW_DOWN                = 0x51
HID_KEY_ARROW_UP                  = 0x52
HID_KEY_ENTER                     = 0x28


BUTTON_A = Pin(2, Pin.IN, Pin.PULL_UP)
BUTTON_B = Pin(1, Pin.IN, Pin.PULL_UP)
JOY_UP = Pin(15, Pin.IN, Pin.PULL_UP)
JOY_DOWN = Pin(16, Pin.IN, Pin.PULL_UP)
JOY_LEFT = Pin(8, Pin.IN, Pin.PULL_UP)
JOY_RIGHT = Pin(7, Pin.IN, Pin.PULL_UP)
JOY_CENTRE = Pin(9, Pin.IN, Pin.PULL_UP)


def joystick_active():
    """Enable USB stack and map buttons A and B to their keyboard counterparts in a busy loop"""
    set_usb_mode()
    while True:
        pressed = []
        if BUTTON_A.value() == 0:
            pressed.append(HID_KEY_A)
        if BUTTON_B.value() == 0:
            pressed.append(HID_KEY_B)
        if JOY_DOWN.value() == 0:
            pressed.append(HID_KEY_ARROW_DOWN)
        if JOY_UP.value() == 0:
            pressed.append(HID_KEY_ARROW_UP)
        if JOY_LEFT.value() == 0:
            pressed.append(HID_KEY_ARROW_LEFT)
        if JOY_RIGHT.value() == 0:
            pressed.append(HID_KEY_ARROW_RIGHT)
        if JOY_CENTRE.value() == 0:
            pressed.append(HID_KEY_ENTER)
        
        # Allow a maximum of 6 scancodes
        pressed = pressed[:6]
        send_key(*pressed)
