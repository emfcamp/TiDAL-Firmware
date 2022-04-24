import time

import tidal
import vga1_8x8 as default_font

class TextWindow:
    BG = tidal.BLUE
    FG = tidal.WHITE

    title = None

    def __init__(self, bg=None, fg=None, font=None):
        if bg is None:
            bg = self.BG
        if fg is None:
            fg = self.FG
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
        self.draw_title()

    def println(self, text="", y=None, fg=None, bg=None, centre=False):
        if y is None:
            y = self.current_line
            self.current_line = self.current_line + 1
        if bg is None:
            bg = self.bg
        if fg is None:
            fg = self.fg
        ypos = self.offset + y * (self.font.HEIGHT + 1)
        self.draw_line(text, ypos, fg, bg, centre)

    def draw_line(self, text, ypos, fg, bg, centre):
        text_width = len(text) * self.font.WIDTH
        w = self.width()
        if centre:
            xpos = (w - text_width) // 2
        else:
            xpos = (w - self.width_chars() * self.font.WIDTH) // 2
        self.display.fill_rect(0, ypos, w, self.font.HEIGHT, bg)
        self.display.text(self.font, text, xpos, ypos, fg, bg)

    def draw_title(self):
        if self.title:
            title_lines = self.title.split("\n")
            for i, line in enumerate(title_lines):
                self.draw_line(line, i * (self.font.HEIGHT + 1), self.fg, self.bg, True)
            liney = len(title_lines) * (self.font.HEIGHT + 1) + 1
            self.display.hline(0, liney, self.width(), self.fg)
            self.offset = liney + 4

    def set_title(self, title):
        self.title = title
        self.draw_title()


    def set_next_line(self, next_line):
        self.current_line = next_line

    def get_next_line(self):
        return self.current_line


class Menu(TextWindow):

    title = "TiDAL Menu"
    _focus_idx = 0

    FOCUS_FG = tidal.BLACK
    FOCUS_BG = tidal.CYAN

    def __init__(self, *args, **kwargs):
        self.focus_fg = kwargs.pop("focus_fg", self.FOCUS_FG)
        self.focus_bg = kwargs.pop("focus_bg", self.FOCUS_BG)
        super().__init__(*args, **kwargs)

    choices = (
        ({"text": "hello"}, lambda: print("hello")),
        ({"text": "Goodbye"}, lambda: print("bye")),
    )

    def choice_line_args(self, idx, focus=False):
        line_info = {
            "y": idx,
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

    def cls(self):
        super().cls()
        for choice, callback in self.choices:
            self.println(**choice)
        if self.choices:
            self.focus_idx = self.focus_idx
