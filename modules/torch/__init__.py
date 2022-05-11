from tidal import *
from app import TextApp

BRIGHTNESS_STEP = 0.8
HUE_STEP = 0.125
HUE_WHITE = -HUE_STEP # special case understood by update_led and hue_step

HUE_RED = 0
HUE_GREEN = 0.3333
HUE_BLUE = 0.6666

# Timings for morse code
MORSE_DOT = 300
MORSE_DASH = 3 * MORSE_DOT
MORSE_WORD = 7 * MORSE_DOT

# Flash patterns for the torch (name, [pattern]), 0 is no flashing
# Where pattern is a list of (time in ms, hue, brightness) tuples
FLASH_PATTERNS = [
    ("None", [(1000, HUE_WHITE, 1.0)]),
    ("Flash", [(200, HUE_WHITE, 1.0), (400, HUE_WHITE, 0)]),
    ("Colours", [(400, HUE_RED, 1.0), (400, HUE_GREEN, 1.0), (400, HUE_BLUE, 1.00)]),
    ("SOS", [(MORSE_DOT, HUE_WHITE, 1.0), (MORSE_DOT, HUE_WHITE, 0), (MORSE_DOT, HUE_WHITE, 1.0), (MORSE_DOT, HUE_WHITE, 0), (MORSE_DOT, HUE_WHITE, 1.0), (MORSE_DOT, HUE_WHITE, 0),
             (MORSE_DASH, HUE_WHITE, 1.0), (MORSE_DOT, HUE_WHITE, 0), (MORSE_DASH, HUE_WHITE, 1.0), (200, HUE_WHITE, 0), (MORSE_DASH, HUE_WHITE, 1.0), (200, HUE_WHITE, 0),
             (MORSE_DOT, HUE_WHITE, 1.0), (MORSE_DOT, HUE_WHITE, 0), (MORSE_DOT, HUE_WHITE, 1.0), (MORSE_DOT, HUE_WHITE, 0), (MORSE_DOT, HUE_WHITE, 1.0), (MORSE_DOT, HUE_WHITE, 0),
             (MORSE_WORD, HUE_WHITE, 0)])
    ]

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


class Torch(TextApp):
    
    TITLE = "Torch"
    BG = st7789.BLACK
    FG = st7789.WHITE

    def update_screen(self, full=True):
        win = self.window
        if full:
            win.println("Press Joystick")
            win.println("or A for on/off.")
            win.println()
            win.println("Joystick up/down")
            win.println("for brightness.")
            win.println()
            win.println("Left/right for")
            win.println("colour.")
            win.println()
            win.println("B for flash mode. ")
            win.println()
            
        win.println("LED: {}".format("ON" if self.state else "OFF"), 12)
        if self.led_h < 0:
            win.println("Colour: WHITE", 13)
        else:
            win.println("Colour: Hue={}'".format(int(self.led_h * 360)), 13)
        win.println("Brightness: {}%".format(int(self.led_v * 100)), 14)
        win.println("Flash:{}  ".format(FLASH_PATTERNS[self.flash_mode][0]), 15)
        win.println("Flash:{} of {}, {} ".format(self.flash_mode, len(FLASH_PATTERNS), self.flash_state), 16)

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
        # Only update the screen if we're in the foreground
        if self.is_active:
            self.update_screen(full=False)

    def toggle_led(self):
        self.flash_stop()
        self.state ^= True
        self.update_led()

    def brightness_up(self):
        self.flash_stop()
        self.state = True
        self.led_v = min((self.led_v * 255) / BRIGHTNESS_STEP, 255) / 255
        self.update_led()

    def brightness_down(self):
        self.flash_stop()
        self.state = True
        self.led_v = ((self.led_v * 255) * BRIGHTNESS_STEP) / 255
        self.update_led()

    def hue_step(self, delta):
        self.flash_stop()
        self.state = True
        # led_h == -HUE_STEP is special case meaning white (saturation=0), so valid range is [-HUE_STEP, 1]
        self.led_h += delta
        if self.led_h >= 1:
            self.led_h = -HUE_STEP
        elif self.led_h < -HUE_STEP:
            self.led_h = 1 - HUE_STEP
        self.update_led()

    def flash_stop(self):
        if self.flash_mode == 0:
            return
        # Turn off flashing
        self.flash_mode = 0
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        # Turn off the LED
        self.state = False
        self.led_h = HUE_WHITE
        self.led_v = 1.0
        self.update_led()

    def flash_change_mode(self):
        self.flash_mode += 1
        self.flash_state = 0
        if self.flash_mode >= len(FLASH_PATTERNS):
            self.flash_stop()
            return
        self.flash_set_state()

    def flash_set_state(self):
        new_state = FLASH_PATTERNS[self.flash_mode][1][self.flash_state]
        if self.timer is not None:
            self.timer.cancel()
        self.timer = self.periodic(new_state[0], self.flash_led_cb)
        self.state = True
        self.led_h = new_state[1]
        self.led_v = new_state[2]
        self.update_led()

    def flash_led_cb(self):
        self.flash_state += 1
        if self.flash_state >= len(FLASH_PATTERNS[self.flash_mode][1]):
            self.flash_state = 0
        self.flash_set_state()

    def on_start(self):
        super().on_start()
        self.state = False
        self.led_h = HUE_WHITE
        self.led_v = 1.0
        self.led = led
        self.timer = None
        self.flash_mode = 0   # Mode we're in.  0 means off.
        self.flash_state = 0  # The part of the pattern we're in
        self.is_active = True

        self.buttons.on_press(JOY_CENTRE, self.toggle_led)
        self.buttons.on_press(BUTTON_A, self.toggle_led)
        self.buttons.on_press(JOY_UP, self.brightness_up)
        self.buttons.on_press(JOY_DOWN, self.brightness_down)
        self.buttons.on_press(JOY_LEFT, lambda: self.hue_step(-HUE_STEP))
        self.buttons.on_press(JOY_RIGHT, lambda: self.hue_step(HUE_STEP))
        self.buttons.on_press(BUTTON_B, self.flash_change_mode)

    def on_activate(self):
        super().on_activate()
        self.is_active = True
        self.update_led()
        self.update_screen()


    def on_deactivate(self):
        super().on_deactivate()
        self.is_active = False






