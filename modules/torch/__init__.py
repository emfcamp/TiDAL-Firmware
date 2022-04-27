from tidal import *
from buttons import Buttons
from textwindow import TextWindow
from app import App, task_coordinator

BRIGHTNESS_STEP = 0.8
HUE_STEP = 0.125
HUE_WHITE = -HUE_STEP # special case understood by update_led and hue_step

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


class Torch(TextWindow, App):
    
    app_id = "torch"
    title = "Torch"
    interval = 0.2
    
    BG = st7789.BLACK
    FG = st7789.WHITE

    def update_screen(self, full=True):
        if full:
            self.cls()
            self.println("Press Joystick")
            self.println("or A for on/off")
            self.println()
            self.println("Joystick up/down")
            self.println("for brightness.")
            self.println()
            self.println("Left/right for")
            self.println("colour.")
            self.println()
            # window.println("B for pattern")
            
        self.println("LED: {}".format("ON" if self.state else "OFF"), 12)
        if self.led_h < 0:
            self.println("Colour: WHITE", 13)
        else:
            self.println("Colour: Hue={}'".format(int(self.led_h * 360)), 13)
        self.println("Brightness: {}%".format(int(self.led_v * 100)), 14)

    def update_led(self):
        if self.led_h >= 0:
            hue = self.led_h
            saturation = 1
        else:
            # White
            hue = 0
            saturation = 0
        # print("LED h={} s={} v={}".format(hue, saturation, led_v))
        led_power_on(self.state)
        if self.state:
            self.led[0] = hsvToRgb(hue, saturation, self.led_v)
        else:
            self.led[0] = (0, 0, 0)
        self.led.write()
        self.update_screen(full=False)

    def toggle_led(self, _):
        self.state ^= True
        self.update_led()

    def brightness_up(self, _):
        self.state = True
        self.led_v = min((self.led_v * 255) / BRIGHTNESS_STEP, 255) / 255
        self.update_led()

    def brightness_down(self, _):
        self.state = True
        self.led_v = ((self.led_v * 255) * BRIGHTNESS_STEP) / 255
        self.update_led()

    def hue_step(self, delta):
        self.state = True
        # led_h == -HUE_STEP is special case meaning white (saturation=0), so valid range is [-HUE_STEP, 1]
        self.led_h += delta
        if self.led_h >= 1:
            self.led_h = -HUE_STEP
        elif self.led_h < -HUE_STEP:
            self.led_h = 1 - HUE_STEP
        self.update_led()

    def on_start(self):
        self.state = False
        self.led_h = HUE_WHITE
        self.led_v = 1.0
        self.buttons = None
        self.led = led

        buttons = Buttons()
        buttons.on_press(JOY_CENTRE, self.toggle_led)
        buttons.on_press(BUTTON_A, self.toggle_led)
        buttons.on_press(JOY_UP, self.brightness_up)
        buttons.on_press(JOY_DOWN, self.brightness_down)
        buttons.on_press(JOY_LEFT, lambda p: self.hue_step(-HUE_STEP))
        buttons.on_press(JOY_RIGHT, lambda p: self.hue_step(HUE_STEP))
        self.buttons = buttons

    def on_wake(self):
        self.update_led()
        self.update_screen()

    def update(self):
        self.buttons.poll()
        self.update_screen(full=False)
        if BUTTON_FRONT.value() == 0:
            task_coordinator.context_changed("menu")

