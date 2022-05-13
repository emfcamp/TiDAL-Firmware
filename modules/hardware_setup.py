# hardware_setup.py Customised for the EMF Camp TiDAL badge

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch, Ihor Nehrutsa

# Supports:
# EMF Camp TiDAL badge 1.14" screen and joystick

from machine import Pin
import gc
from drivers.st7789.st7789_passthrough import *
SSD = ST7789Passthrough

mode = PORTRAIT  # Options PORTRAIT, USD, REFLECT combined with |

gc.collect()  # Precaution before instantiating framebuf

portrait = mode & PORTRAIT
ht, wd = (240, 135) if portrait else (135, 240)
ssd = SSD(None, height=ht, width=wd, dc=None, cs=None, rst=None, disp_mode=mode)

# Create and export a Display instance
from gui.core.ugui import Display
# Define control buttons: adjust joystick orientation to match display
# Orientation is only correct for basic LANDSCAPE and PORTRAIT modes
pnxt, pprev, pin, pdec = (7, 8, 15, 16) if portrait else (15, 16, 7, 8)
nxt = Pin(pnxt, Pin.IN, Pin.PULL_UP)  # Move to next control
sel = Pin(9, Pin.IN, Pin.PULL_UP)  # Operate current control
prev = Pin(pprev, Pin.IN, Pin.PULL_UP)  # Move to previous control
increase = Pin(pin, Pin.IN, Pin.PULL_UP)  # Increase control's value
decrease = Pin(pdec, Pin.IN, Pin.PULL_UP)  # Decrease control's value
display = Display(ssd, nxt, sel, prev, increase, decrease)
