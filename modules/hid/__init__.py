from tidal import *
from app import TextApp
from joystick import HID_KEY_A, HID_KEY_B, HID_KEY_ARROW_UP, HID_KEY_ARROW_DOWN, HID_KEY_ARROW_LEFT, HID_KEY_ARROW_RIGHT, HID_KEY_ENTER
from scheduler import get_scheduler
from textwindow import TextWindow
import vga2_16x16 as font

CENTRE_X = (135 - font.WIDTH) // 2
CENTRE_Y = (240 - font.HEIGHT) // 2

class USBKeyboard(TextApp):

    BG = WHITE
    FG = BLACK
    TITLE = "USB Keyboard"

    keys = {
        HID_KEY_A: (135 - font.WIDTH, 180, "A"),
        HID_KEY_B: (0, 240 - font.HEIGHT, "B"),
        HID_KEY_ARROW_UP: (CENTRE_X, CENTRE_Y - font.HEIGHT, TextWindow.UP_ARROW),
        HID_KEY_ARROW_DOWN: (CENTRE_X, CENTRE_Y + font.HEIGHT, TextWindow.DOWN_ARROW),
        HID_KEY_ARROW_LEFT: (CENTRE_X - font.WIDTH, CENTRE_Y, TextWindow.LEFT_ARROW),
        HID_KEY_ARROW_RIGHT: (CENTRE_X + font.WIDTH, CENTRE_Y, TextWindow.RIGHT_ARROW),
        HID_KEY_ENTER: (CENTRE_X, CENTRE_Y, "\x09"),
    }

    def __init__(self):
        super().__init__()
        self.pressed = set()

    def on_start(self):
        super().on_start()
        self.buttons.on_up_down(BUTTON_A, lambda down: self.send_key(HID_KEY_A, down))
        self.buttons.on_up_down(BUTTON_B, lambda down: self.send_key(HID_KEY_B, down))
        self.buttons.on_up_down(JOY_DOWN, lambda down: self.send_key(HID_KEY_ARROW_DOWN, down))
        self.buttons.on_up_down(JOY_UP, lambda down: self.send_key(HID_KEY_ARROW_UP, down))
        self.buttons.on_up_down(JOY_LEFT, lambda down: self.send_key(HID_KEY_ARROW_LEFT, down))
        self.buttons.on_up_down(JOY_RIGHT, lambda down: self.send_key(HID_KEY_ARROW_RIGHT, down))
        self.buttons.on_up_down(JOY_CENTRE, lambda down: self.send_key(HID_KEY_ENTER, down))

    def on_activate(self):
        super().on_activate()

        r = 34
        x = CENTRE_X + (font.WIDTH // 2)
        y = CENTRE_Y + (font.HEIGHT // 2)
        poly = [
            (x, y - r),
            (x + r, y),
            (x, y + r),
            (x - r, y),
            (x, y - r)
        ]
        display.polygon(poly, 0, 0, self.FG)

        (ax, ay, _) = self.keys[HID_KEY_A]
        a_box = [
            (ax + font.WIDTH - 1, ay - 1),
            (ax - 1, ay - 1),
            (ax - 1, ay + font.HEIGHT),
            (ax + font.WIDTH - 1, ay + font.HEIGHT)
        ]
        display.polygon(a_box, 0, 0, self.FG)

        (bx, by, _) = self.keys[HID_KEY_B]
        b_box = [
            (bx, by - 1),
            (bx + font.WIDTH, by - 1),
            (bx + font.WIDTH, by + font.HEIGHT),
        ]
        display.polygon(b_box, 0, 0, self.FG)

        for k in self.keys.keys():
            self.draw_key(k, False)

    def draw_key(self, k, down):
        (x, y, text) = self.keys[k]
        fg = self.window.bg if down else self.window.fg
        bg = self.window.fg if down else self.window.bg
        self.window.draw_text(text, x, y, fg, bg, font)

    def send_key(self, k, down):
        self.draw_key(k, down)

        if down:
            self.pressed.add(k)
        else:
            self.pressed.discard(k)

        usb.hid.send_key(*self.pressed)
