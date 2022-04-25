import tidal
import vga1_8x8 as default_font

class TextWindow:
    def __init__(self, bg=None, fg=None, title=None, font=None):
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
        if title:
            self.title = title

    def width(self):
        return self.display.width()

    def height(self):
        return self.display.height()

    def width_chars(self):
        return self.display.width() // self.font.WIDTH

    def height_chars(self):
        return self.display.height() // self.font.HEIGHT

    def cls(self):
        self.display.fill(self.bg)
        self.current_line = 0
        self.draw_title()

    def clear_from_line(self, line=None):
        if line is None:
            line = self.get_next_line()
        else:
            # Passing in a line also updates next_line
            self.set_next_line(line)
        y = self.get_line_pos(line)
        h = self.height() - y
        self.display.fill_rect(0, y, self.width(), h, self.bg)

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

    def get_line_pos(self, line):
        return self.offset + line * (self.font.HEIGHT + 1)

class Menu(TextWindow):

    _focus_idx = 0

    def __init__(self, bg, fg, focus_bg, focus_fg, title, choices, font=None):
        super().__init__(bg, fg, title, font)
        self.focus_fg = focus_fg
        self.focus_bg = focus_bg
        self.choices = choices

    def choice_line_args(self, idx, focus=False):
        line_info = {
            "y": idx,
            "fg": self.focus_fg if focus else self.fg,
            "bg": self.focus_bg if focus else self.bg,
            "centre": False
        }
        line_info.update(self.choices[idx][0])
        return line_info

    def focus_idx(self):
        return self._focus_idx

    def set_focus_idx(self, i):
        self.println(**self.choice_line_args(self._focus_idx, focus=False))
        self._focus_idx = i % len(self.choices)
        self.println(**self.choice_line_args(self._focus_idx, focus=True))

    def cls(self):
        super().cls()
        for choice, callback in self.choices:
            self.println(**choice)
        if self.choices:
            # Force redraw of highlight
            self.set_focus_idx(self._focus_idx)
