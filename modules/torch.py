from tidal import *
from neopixel import NeoPixel
import buttons
from textwindow import TextWindow

BRIGHTNESS_STEP = 0.8
HUE_STEP = 0.125
HUE_WHITE = -HUE_STEP # special case understood by update_led and hue_step

window = None
led = NeoPixel(LED_DATA, 1)
state = False

led_h = HUE_WHITE
led_v = 1.0

# Ported from https://axonflux.com/handy-rgb-to-hsl-and-rgb-to-hsv-color-model-c
def hsvToRgb(h, s, v):
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    mod = i % 6
    if mod == 0:
        r = v; g = t; b = p
    elif mod == 1:
        r = q; g = v; b = p
    elif mod == 2:
        r = p; g = v; b = t
    elif mod == 3:
        r = p; g = q; b = v
    elif mod == 4:
        r = t; g = p; b = v
    elif mod == 5:
        r = v; g = p; b = q

    return (int(r * 255), int(g * 255), int(b * 255))

def rgbToHsv(r, g, b):
    r = r / 255
    g = g / 255
    b = b / 255
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    v = max_val
    d = max_val - min_val
    s = 0 if max_val == 0 else d / max_val

    if max_val == min_val:
        h = 0 # achromatic
    else:
        if max_val == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_val == g:
            h = (b - r) / d + 2
        elif max_val == b:
            h = (r - g) / d + 4
        h /= 6

    return (h, s, v)

def update_screen():
    window.println("LED: {}".format("ON" if state else "OFF"), 12)
    if led_h < 0:
        window.println("Colour: WHITE", 13)
    else:
        window.println("Colour: Hue={}'".format(int(led_h * 360)), 13)
    window.println("Brightness: {}%".format(int(led_v * 100)), 14)

def update_led():
    if led_h >= 0:
        hue = led_h
        saturation = 1
    else:
        # White
        hue = 0
        saturation = 0
    # print("LED h={} s={} v={}".format(hue, saturation, led_v))
    LED_PWREN.value(state and 0 or 1)
    if state:
        led[0] = hsvToRgb(hue, saturation, led_v)
    else:
        led[0] = (0, 0, 0)
    led.write()
    update_screen()

def toggle_led(_):
    global state
    state = not state
    update_led()

def brightness_up(_):
    global state, led_v
    state = True
    led_v = min((led_v * 255) / BRIGHTNESS_STEP, 255) / 255
    update_led()

def brightness_down(_):
    global state, led_v
    state = True
    led_v = ((led_v * 255) * BRIGHTNESS_STEP) / 255
    update_led()

def hue_step(delta):
    global state, led_h
    state = True
    # led_h == -HUE_STEP is special case meaning white (saturation=0), so valid range is [-HUE_STEP, 1]
    led_h = led_h + delta
    if led_h >= 1:
        led_h = -HUE_STEP
    elif led_h < -HUE_STEP:
        led_h = 1 - HUE_STEP

    update_led()

def main():
    global window
    window = TextWindow(BLACK, WHITE)
    update_led()

    window.cls()
    window.println("-----Torch------")
    window.println("Press Joystick")
    window.println("or A for on/off")
    window.println()
    window.println("Joystick up/down")
    window.println("for brightness.")
    window.println()
    window.println("Left/right for")
    window.println("colour.")
    window.println()
    # window.println("B for pattern")
    update_screen()

    buttons.on_press(JOY_CENTRE, toggle_led)
    buttons.on_press(BUTTON_A, toggle_led)
    buttons.on_press(JOY_UP, brightness_up)
    buttons.on_press(JOY_DOWN, brightness_down)
    buttons.on_press(JOY_LEFT, lambda p: hue_step(-HUE_STEP))
    buttons.on_press(JOY_RIGHT, lambda p: hue_step(HUE_STEP))

    buttons.poll()
