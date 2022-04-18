from machine import I2C
from machine import Pin
from machine import SPI
import st7789
from st7789 import BLACK, BLUE, RED, GREEN, CYAN, MAGENTA, YELLOW, WHITE

import _tidal_usb as usb


G0 = Pin(18, Pin.IN)
G1 = Pin(17, Pin.IN)
G2 = Pin(4, Pin.IN)
G3 = Pin(5, Pin.IN)

BUTTON_A = Pin(2, Pin.IN, Pin.PULL_UP)
BUTTON_B = Pin(1, Pin.IN, Pin.PULL_UP)
JOY_UP = Pin(15, Pin.IN, Pin.PULL_UP)
JOY_DOWN = Pin(16, Pin.IN, Pin.PULL_UP)
JOY_LEFT = Pin(8, Pin.IN, Pin.PULL_UP)
JOY_RIGHT = Pin(7, Pin.IN, Pin.PULL_UP)
JOY_CENTRE = Pin(9, Pin.IN, Pin.PULL_UP)

all_buttons = [
    BUTTON_A,
    BUTTON_B,
    JOY_UP,
    JOY_DOWN,
    JOY_LEFT,
    JOY_RIGHT,
    JOY_CENTRE,
]

LED_PWREN = Pin(3, Pin.OUT)
LED_DATA = Pin(46, Pin.OUT)
# LED_DATA = Pin(48, Pin.OUT) # esp32s3 devkit

LCD_PWR =  Pin(39, Pin.OUT)
LCD_BLEN = Pin(0, Pin.OUT)

CHARGE_DET = Pin(26, Pin.IN, Pin.PULL_UP)

AUTH_WAKE = Pin(21, Pin.OUT)

i2c = I2C(scl=Pin(41), sda=Pin(42))


LCD_CS = Pin(10, Pin.OUT)
LCD_CLK = Pin(12)
LCD_DIN = Pin(11)
LCD_SPI = SPI(2, baudrate=120000000, polarity=1, sck=LCD_CLK, mosi=LCD_DIN)
LCD_RESET = Pin(14, Pin.OUT)
LCD_DC = Pin(13, Pin.OUT)

display = st7789.ST7789(LCD_SPI, 135, 240, reset=LCD_RESET, dc=LCD_DC, rotation=2)

def init_lcd():
    LCD_CS.off()
    display.init()


def lcd_fps() -> int:
    import time
    import random
    frames = 0
    start = time.ticks_us()
    end = start + 1000000
    while time.ticks_us() < end:
        c = random.choice([st7789.RED, st7789.GREEN, st7789.BLUE, st7789.CYAN, st7789.MAGENTA])
        display.fill(c)
        frames += 1
    return frames
