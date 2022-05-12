from tidal import *
from app import App
from buttons import Buttons
from textwindow import TextWindow
import settings
import vga2_bold_16x32

DEFAULT_NAME = "Insert name\nhere"

class Hello(App):
    
    def __init__(self):
        super().__init__()
        window = HelloWindow(settings.get("hello_name"))
        self.push_window(window, activate=False)

    def supports_rotation(self):
        return True

    def on_start(self):
        super().on_start()
        self.buttons.on_press(BUTTON_B, self.rotate)
        self.buttons.on_press(JOY_CENTRE, self.edit_name)

    def rotate(self):
        self.set_rotation((self.get_rotation() + 90) % 360)

    def edit_name(self):
        new_name = self.keyboard_prompt("Set name:", self.window.name, multiline_allowed=True)
        if new_name != self.window.name:
            settings.set("hello_name", new_name)
            self.window.name = new_name
            self.window.redraw()
            settings.save()


class HelloWindow(TextWindow):

    def __init__(self, name):
        super().__init__(RED, WHITE, None, None, Buttons())
        self.name = name

    def redraw(self):
        self.println("HELLO", 0, centre=True)
        self.println("my name is", 1, centre=True)
        y = self.get_line_pos(2)
        BOTTOM_BAR_H = 10
        h = self.height() - (y - self.pos_y) - BOTTOM_BAR_H

        display = self.display
        name_font = vga2_bold_16x32
        lines = self.flow_lines(self.name or DEFAULT_NAME, name_font)

        display.fill_rect(0, y, self.width(), h, WHITE)
        texth = name_font.HEIGHT * len(lines)
        texty = y + (h - texth) // 2
        for (i, line) in enumerate(lines):
            textw = len(line) * name_font.WIDTH
            linex = (self.width() - textw) // 2
            liney = texty + (i * name_font.HEIGHT)
            self.draw_text(line, linex, liney, BLACK, WHITE, name_font)
        display.fill_rect(0, y + h, self.width(), BOTTOM_BAR_H, RED)
