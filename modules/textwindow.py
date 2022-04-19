import time

import tidal
import vga1_8x8 as default_font

class TextWindow:

    def __init__(self, bg=None, fg=None, font=None):
        if bg is None:
            bg = tidal.BLUE
        if fg is None:
            fg = tidal.WHITE
        if font is None:
            font = default_font
        self.bg = bg
        self.fg = fg
        self.font = font
        self.current_line = 0
        self.offset = 0
        self.display = tidal.display

    def width(self):
        return self.display.width()

    def height(self):
        return self.display.height()

    def width_chars(self):
        return self.display.width() // self.font.WIDTH

    def height_chars(self):
        return self.display.height() // self.font.HEIGHT

    def cls(self, colour=None):
        if colour is None:
            colour = self.bg
        self.display.fill(colour)
        self.current_line = 0

    def println(self, text="", y=None, fg=None, bg=None, centre=False):
        if y is None:
            y = self.current_line
            self.current_line = self.current_line + 1
        if bg is None:
            bg = self.bg
        if fg is None:
            fg = self.fg
        ypos = self.offset + y * (self.font.HEIGHT + 1)
        xpos = 0
        text_width = len(text) * self.font.WIDTH
        if centre:
            xpos = (self.width() - text_width) // 2
            self.display.fill_rect(0, ypos, xpos, self.font.HEIGHT, bg)
        # num_spaces is more than needed if centred, doesn't matter
        num_spaces = self.width_chars() - len(text)
        self.display.text(self.font, text + (" " * num_spaces), xpos, ypos, fg, bg)

    def run_sync(self):
        self.cls()

class Menu(TextWindow):

    title = "TiDAL Boot Menu"
    _focus_idx = 0
    focus_fg = tidal.BLACK
    focus_bg = tidal.CYAN

    choices = (
        ({"text": "hello"}, lambda: print("hello")),
        ({"text": "Goodbye"}, lambda: print("bye")),
    )

    def choice_line_args(self, idx, focus=False):
        y_offset = len(self.header_rows)
        line_info = {
            "y": y_offset + idx,
            "fg": self.focus_fg if focus else self.fg,
            "bg": self.focus_bg if focus else self.bg,
            "centre": False
        }
        line_info.update(self.choices[idx][0])
        return line_info

    @property
    def focus_idx(self):
        return self._focus_idx

    @focus_idx.setter
    def focus_idx(self, i):
        if i < 0 or i >= len(self.choices):
            i = 0
        self.println(**self.choice_line_args(self._focus_idx, focus=False))
        self._focus_idx = i
        self.println(**self.choice_line_args(self._focus_idx, focus=True))

    @property
    def header_rows(self):
        return (
            {"text": "EMF 2022", "centre": True},
            {"text": self.title},
            {"text": "-" * self.width_chars()}
        )

    def cls(self):
        super().cls()
        for header in self.header_rows:
            self.println(**header)
        for choice, callback in self.choices:
            self.println(**choice)
        if self.choices:
            self.focus_idx = self.focus_idx

    def run_sync(self):
        self.cls()
        initial_item = 0
        try:
            with open("lastbootitem.txt", "rt", encoding="ascii") as f:
                initial_item = int(f.read())
        except:
            pass

        if initial_item < 0 or initial_item >= len(self.choices):
            initial_item = 0
        self.focus_idx = initial_item

        while True:
            if tidal.JOY_DOWN.value() == 0:
                self.focus_idx += 1
            elif tidal.JOY_UP.value() == 0:
                self.focus_idx -= 1
            elif any((
                    tidal.BUTTON_A.value() == 0,
                    tidal.BUTTON_B.value() == 0,
                    tidal.JOY_CENTRE.value() == 0,
                )):
                with open("lastbootitem.txt", "wt", encoding="ascii") as f:
                    f.write(str(self.focus_idx))
                self.choices[self.focus_idx][1]()

            time.sleep(0.2)
