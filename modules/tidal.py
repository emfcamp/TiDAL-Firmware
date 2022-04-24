from machine import I2C
from machine import Pin
from machine import SPI
from neopixel import NeoPixel
import st7789
from st7789 import BLACK, BLUE, RED, GREEN, CYAN, MAGENTA, YELLOW, WHITE

import _tidal_usb as usb

_devkitpins={}

_devkitpins["BTN_A"]=2
_devkitpins["BTN_B"]=1
_devkitpins["BTN_FRONT"]=6
_devkitpins["JUP"]=15
_devkitpins["JDOWN"]=16
_devkitpins["JLEFT"]=8
_devkitpins["JRIGHT"]=7
_devkitpins["JCENT"]=9
_devkitpins["G0"]=18
_devkitpins["G1"]=17
_devkitpins["G2"]=4
_devkitpins["G3"]=5
_devkitpins["LED_DATA"] = 48
_devkitpins["LED_PWREN"] = 3
_devkitpins["LCD_PWR"] = 48
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


_proto1pins={}
_productionpins={}

for i in _devkitpins:
    _proto1pins[i]=_devkitpins[i]
    _productionpins[i]=_devkitpins[i]

_proto1pins["LED_DATA"] = 46
_productionpins["LED_DATA"] = 46
_proto1pins["CHARGE_DET"] = 26
_productionpins["CHARGE_DET"] = 21


#_hw=_devkitpins
_hw=_proto1pins
#_hw=_productionpins

G0 = Pin(_hw["G0"], Pin.IN)
G1 = Pin(_hw["G1"], Pin.IN)
G2 = Pin(_hw["G2"], Pin.IN)
G3 = Pin(_hw["G3"], Pin.IN)

BUTTON_A = Pin(_hw["BTN_A"], Pin.IN, Pin.PULL_UP)
BUTTON_B = Pin(_hw["BTN_B"], Pin.IN, Pin.PULL_UP)
BUTTON_FRONT = Pin(_hw["BTN_FRONT"], Pin.IN, Pin.PULL_UP)
JOY_UP = Pin(_hw["JUP"], Pin.IN, Pin.PULL_UP)
JOY_DOWN = Pin(_hw["JDOWN"], Pin.IN, Pin.PULL_UP)
JOY_LEFT = Pin(_hw["JLEFT"], Pin.IN, Pin.PULL_UP)
JOY_RIGHT = Pin(_hw["JRIGHT"], Pin.IN, Pin.PULL_UP)
JOY_CENTRE = Pin(_hw["JCEN"], Pin.IN, Pin.PULL_UP)

all_buttons = [
    BUTTON_A,
    BUTTON_B,
    BUTTON_FRONT,
    JOY_UP,
    JOY_DOWN,
    JOY_LEFT,
    JOY_RIGHT,
    JOY_CENTRE,
]

_LED_PWREN = Pin(_hw["LED_PWREN"], Pin.OUT, value=1)
LED_DATA = Pin(_hw["LED_DATA"], Pin.OUT)

_LCD_PWR =  Pin(_hw["LCD_PWR"], Pin.OUT)
_LCD_BLEN = Pin(_hw["LCD_BLEN"], Pin.OUT)

led=NeoPixel(_hw["LED_DATA"], 1)

Pin(_hw["UVLO_TRIG"], Pin.OUT)

def system_power_off():
    uvlotrig=Pin(_hw["UVLO_TRIG"], Pin.OUT)
    uvlotrig.on()

def led_power_on(on=True):
    if(on):
        _LED_PWREN.off()
    else:
        _LED_PWREN.on()

def led_power_off():
    led_power_on(False)


def lcd_power_on(on=True):
    if(on):
        _LCD_PWR.off()
    else:
        _LCD_PWR.on()

def lcd_power_off():
    lcd_power_on(False)

def lcd_backlight_on(on=True):
    if(on):
        _LED_PWREN.init(mode=Pin.OUT,value=1)
    else:
        _LED_PWREN.init(mode=Pin.IN,pull=None)
        
def lcd_backlight_off():
    lcd_backlight_on(False)

CHARGE_DET = Pin(_hw["CHARGE_DET"], Pin.IN, Pin.PULL_UP)

i2cs = I2C(scl=Pin(_hw["SCL_S"]), sda=Pin(_hw["SDA_S"]))
i2cp = I2C(scl=Pin(_hw["SCL_P"]), sda=Pin(_hw["SDA_P"]))

i2c = i2cs

LCD_CS = Pin(_hw["LCD_CS"], Pin.OUT)
LCD_CLK = Pin(_hw["LCD_CLK"])
LCD_DIN = Pin(_hw["LCD_DIN"])
LCD_SPI = SPI(2, baudrate=40000000, polarity=1, sck=LCD_CLK, mosi=LCD_DIN)
LCD_RESET = Pin(_hw["LCD_RESET"], Pin.OUT)
LCD_DC = Pin(_hw["LCD_DC"], Pin.OUT)

display = st7789.ST7789(LCD_SPI, 135, 240, reset=LCD_RESET, dc=LCD_DC, rotation=2)

def init_lcd():
    LCD_CS.off()
    display.init()
    # Set up scrolling parameters, if anyone wants to use them
    display.vscrdef(40, 240, 40)
    display.vscsad(40)


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
