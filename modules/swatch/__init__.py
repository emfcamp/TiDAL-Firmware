from tidal import display, BLACK, WHITE
import tidal
from app import TextApp
import vga2_8x8 as font

class Swatch(TextApp):

    r = 0x15
    g = 0x17
    b = 0x35

    def redraw(self):
        print(f"#{self.r:02X}{self.g:02X}{self.b:02X}")
        display.fill_rect(0, 0, display.width(), display.height(), tidal.color565(self.r, self.g, self.b))
        display.text(font, f"#{self.r:02X}{self.g:02X}{self.b:02X}", 0, 0, BLACK, WHITE)

    def on_start(self):
        super().on_start()
        buttons = self.window.buttons
        buttons.on_press(tidal.JOY_DOWN, lambda: self.set_r(self.r - 1))
        buttons.on_press(tidal.JOY_UP, lambda: self.set_r(self.r + 1))
        buttons.on_press(tidal.JOY_LEFT, lambda: self.set_g(self.g - 1))
        buttons.on_press(tidal.JOY_RIGHT, lambda: self.set_g(self.g + 1))
        buttons.on_press(tidal.BUTTON_B, lambda: self.set_b(self.b - 1))
        buttons.on_press(tidal.BUTTON_A, lambda: self.set_b(self.b + 1))

    def on_activate(self):
        super().on_activate()
        self.redraw()

    def set_r(self, val):
        self.r = val % 256
        self.redraw()

    def set_g(self, val):
        self.g = val % 256
        self.redraw()

    def set_b(self, val):
        self.b = val % 256
        self.redraw()
