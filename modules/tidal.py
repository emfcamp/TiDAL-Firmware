import machine
from machine import I2C, SoftI2C
from machine import Pin
from machine import SPI
from neopixel import NeoPixel
import st7789
from st7789 import BLACK, BLUE, RED, GREEN, CYAN, MAGENTA, YELLOW, WHITE, color565

import _tidal_usb as usb
import tidal_helpers


"""
NOTE: If you are using the automatic lightsleep (on by default) you should never
leave any pins set to input without a pullup unless they are guaranteed not to change state
(externally held high/low).

This affects pins G0, G1, G2, G3 (GPIO18,GPIO17,GPIO4,GPIO5 respectively).
"""

_devkitpins={}

_devkitpins["BTN_A"]=2
_devkitpins["BTN_B"]=1
_devkitpins["BTN_FRONT"]=6
_devkitpins["JUP"]=15
_devkitpins["JDOWN"]=16
_devkitpins["JLEFT"]=8
_devkitpins["JRIGHT"]=7
_devkitpins["JCEN"]=9
_devkitpins["G0"]=18
_devkitpins["G1"]=17
_devkitpins["G2"]=4
_devkitpins["G3"]=5
_devkitpins["LED_DATA"] = 48
_devkitpins["LED_PWREN"] = 3
_devkitpins["LCD_PWR"] = 39
_devkitpins["LCD_BLEN"] = 0
_devkitpins["SCL_S"] = 41
_devkitpins["SDA_S"] = 42
_devkitpins["SCL_P"] = 43
_devkitpins["SDA_P"] = 44
_devkitpins["LCD_CS"] = 10
_devkitpins["LCD_CLK"] = 12
_devkitpins["LCD_DIN"] = 11
_devkitpins["LCD_RESET"] = 14
_devkitpins["LCD_DC"] = 13
_devkitpins["UVLO_TRIG"] = 45
_devkitpins["ACCEL_INT"] = 40

# This isn't a real pin definition, it's just so there's a pin-like
# object for charge det
_devkitpins["CHARGE_DET"] = 47


_proto1pins={}
_productionpins={}

for i in _devkitpins:
    _proto1pins[i]=_devkitpins[i]
    _productionpins[i]=_devkitpins[i]

_proto1pins["LED_DATA"] = 46
_productionpins["LED_DATA"] = 46
_proto1pins["CHARGE_DET"] = 26
_productionpins["CHARGE_DET"] = 21


variant = tidal_helpers.get_variant()
if variant == "devboard":
    _hw = _devkitpins
elif variant == "prototype":
    _hw = _proto1pins
else:
    _hw = _productionpins

G0 = Pin(_hw["G0"], Pin.IN, Pin.PULL_UP)
G1 = Pin(_hw["G1"], Pin.IN, Pin.PULL_UP)
G2 = Pin(_hw["G2"], Pin.IN, Pin.PULL_UP)
G3 = Pin(_hw["G3"], Pin.IN, Pin.PULL_UP)

BUTTON_A = Pin(_hw["BTN_A"], Pin.IN, Pin.PULL_UP)
BUTTON_B = Pin(_hw["BTN_B"], Pin.IN, Pin.PULL_UP)
BUTTON_FRONT = Pin(_hw["BTN_FRONT"], Pin.IN, Pin.PULL_UP)
JOY_UP = Pin(_hw["JUP"], Pin.IN, Pin.PULL_UP)
JOY_DOWN = Pin(_hw["JDOWN"], Pin.IN, Pin.PULL_UP)
JOY_LEFT = Pin(_hw["JLEFT"], Pin.IN, Pin.PULL_UP)
JOY_RIGHT = Pin(_hw["JRIGHT"], Pin.IN, Pin.PULL_UP)
JOY_CENTRE = Pin(_hw["JCEN"], Pin.IN, Pin.PULL_UP)

ALL_BUTTONS = [
    BUTTON_A,
    BUTTON_B,
    BUTTON_FRONT,
    JOY_UP,
    JOY_DOWN,
    JOY_LEFT,
    JOY_RIGHT,
    JOY_CENTRE,
]

_LCD_RESET = Pin(_hw["LCD_RESET"], Pin.OUT)

_LED_PWREN = Pin(_hw["LED_PWREN"], Pin.OUT, value=1)
LED_DATA = Pin(_hw["LED_DATA"], Pin.OUT)

_LCD_PWR_ALWAYS =  Pin(_hw["LCD_PWR"], Pin.OUT, value=0)
_LCD_BLEN = Pin(_hw["LCD_BLEN"], Pin.OUT, drive=Pin.DRIVE_0, value=0)

led=NeoPixel(LED_DATA, 1)

_UVLO_TRIG = Pin(_hw["UVLO_TRIG"], Pin.OUT)

def system_power_off():
    _UVLO_TRIG.on()

def led_power_on(on=True):
    if on:
        _LED_PWREN.off()
    else:
        _LED_PWREN.on()

_lcd_is_on = True

def led_power_off():
    led_power_on(False)

def lcd_power_on(on=True):
    global _lcd_is_on
    if on:
        display.sleep_mode(0)
        lcd_backlight_on()
    else:
        lcd_backlight_off()
        display.sleep_mode(1)
    _lcd_is_on = on

def lcd_power_off():
    lcd_power_on(False)

def lcd_is_on():
    return _lcd_is_on

def lcd_backlight_on(on=True):
    if on:
        _LCD_BLEN.init(mode=Pin.OUT, drive=Pin.DRIVE_0, value=0)
    else:
        _LCD_BLEN.init(mode=Pin.IN, pull=Pin.PULL_UP)
        
def lcd_backlight_off():
    lcd_backlight_on(False)

CHARGE_DET = Pin(_hw["CHARGE_DET"], Pin.IN, Pin.PULL_UP)

i2cs = SoftI2C(scl=Pin(_hw["SCL_S"]), sda=Pin(_hw["SDA_S"]))

i2cp = None

def enable_peripheral_I2C():
    global i2cp
    i2cp=I2C(scl=Pin(_hw["SCL_P"]), sda=Pin(_hw["SDA_P"]))

i2c = i2cs

_LCD_CS = Pin(_hw["LCD_CS"], Pin.OUT)
_LCD_CLK = Pin(_hw["LCD_CLK"])
_LCD_DIN = Pin(_hw["LCD_DIN"])
_LCD_SPI = SPI(2, baudrate=40000000, polarity=1, sck=_LCD_CLK, mosi=_LCD_DIN)

_LCD_DC = Pin(_hw["LCD_DC"], Pin.OUT)

display = st7789.ST7789(_LCD_SPI, 135, 240, reset=_LCD_RESET, dc=_LCD_DC, rotation=2)

def init_lcd():
    _LCD_PWR_ALWAYS.off() # this is mandatory even if LCD is disabled using lcd_power_off() - having this pin high significantly increases power consumption
    lcd_backlight_on()
    _LCD_CS.off()
    display.init()
    # Set up scrolling parameters, if anyone wants to use them
    display.vscrdef(40, 240, 40)
    display.vscsad(40)

# Mapping of angles (as used by App and Buttons) to display params
_DISPLAY_ROTATIONS = { 0: 2, 90: 1, 180: 0, 270: 3 }
_display_rotation = 0 # as an angle

def set_display_rotation(rotation):
    global _display_rotation
    if rotation != _display_rotation:
        _display_rotation = rotation
        display.rotation(_DISPLAY_ROTATIONS[rotation])

def get_display_rotation():
    return _display_rotation

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

def power_test_sequence(): #value without/with DFS
    import time, emf_png
    display.bitmap(emf_png, 0, 0)#39/32mA
    time.sleep(5)
    lcd_backlight_off()#29/22
    time.sleep(5)
    lcd_power_off()#23/16
    time.sleep(5)
    lcd_power_on()#39/32
    time.sleep(5)
    lcd_power_off()
    machine.lightsleep(5000)#2.3/2.2
    lcd_power_on()
    time.sleep(1)
    lcd_fps()#?/60
    lcd_fps()
    lcd_fps()
    lcd_fps()
    machine.lightsleep(5000)#lightsleep with display -> ?/18mA
    time.sleep(0.1)
    machine.deepsleep(5000)#0.1
