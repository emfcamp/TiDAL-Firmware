# hardware_setup.py Customised for the EMF Camp TiDAL badge

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch, Ihor Nehrutsa

# Supports:
# EMF Camp TiDAL badge 1.14" screen and joystick

from machine import Pin
import gc
import tidal
from st7789_passthrough import *
SSD = ST7789Passthrough

gc.collect()  # Precaution before instantiating framebuf

ssd = SSD()

# Create and export a Display instance
from gui.core.ugui import Display

class DummyInput:
    def precision(self, val):
        pass

    def adj_mode(self, v=None):
        pass

    def is_adjust(self):
        return False

    def is_precision(self):
        return False

    def encoder(self):
        return True # Nonsense but makes the code not try to be smart about handling button autorepeat itself

class NoInputDisplay(Display):
    def __init__(self, objssd):
        # Note, does NOT call super
        self.ipdev = DummyInput()
        self.height = objssd.height
        self.width = objssd.width
        self._is_grey = False

display = NoInputDisplay(ssd)
