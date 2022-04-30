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
        self.display.fill_rect(0, ypos, w, self.font.HEIGHT + 1, bg)
        self.display.text(self.font, text, xpos, ypos, fg, bg)

    def draw_title(self):
        if self.title:
            title_lines = self.title.split("\n")
            for i, line in enumerate(title_lines):
                self.draw_line(line, i * (self.font.HEIGHT + 1), self.fg, self.bg, True)
            liney = len(title_lines) * (self.font.HEIGHT + 1)
            w = self.width()
            self.display.fill_rect(0, liney, w, 1, self.bg)
            self.display.hline(0, liney + 1, w, self.fg)
            self.display.fill_rect(0, liney + 2, w, 3, self.bg)
            self.offset = liney + 5

    def set_title(self, title):
        self.title = title
        self.draw_title()

    def set_next_line(self, next_line):
        self.current_line = next_line

    def get_next_line(self):
        return self.current_line

    def get_line_pos(self, line):
        return self.offset + line * (self.font.HEIGHT + 1)

    def progress_bar(self, line, percentage, fg=None):
        """Display a line-sized progress bar for a percentage value 0-100"""
        if fg is None:
            fg = self.fg
        x = (self.width() - 100) // 2
        y = self.get_line_pos(line)
        self.display.fill_rect(x, y, percentage, self.font.HEIGHT, fg)
        # In case progress goes down, clear the right-hand side of the line
        self.display.fill_rect(x + percentage, y, self.width() - (x + percentage), self.font.HEIGHT, self.bg)

class Menu(TextWindow):

    def __init__(self, bg, fg, focus_bg, focus_fg, title, choices, font=None):
        super().__init__(bg, fg, title, font)
        self.focus_fg = focus_fg
        self.focus_bg = focus_bg
        self.choices = choices
        self._focus_idx = 0

    def choice_line_args(self, idx, focus=False):
        line_info = {
            "y": idx,
            "fg": self.focus_fg if focus else self.fg,
            "bg": self.focus_bg if focus else self.bg,
            "centre": False
        }
        args = self.choices[idx][0]
        if isinstance(args, str):
            args = { "text": args }
        line_info.update(args)
        return line_info

    def focus_idx(self):
        return self._focus_idx

    def set_focus_idx(self, i, redraw=True):
        if redraw:
            self.println(**self.choice_line_args(self._focus_idx, focus=False))
        self._focus_idx = i % len(self.choices)
        if redraw:
            self.println(**self.choice_line_args(self._focus_idx, focus=True))

    def draw_choices(self):
        for i in range(len(self.choices)):
            self.println(**self.choice_line_args(i, focus=(i == self._focus_idx)))

    def cls(self):
        self.draw_title()
        self.draw_choices()
        self.clear_from_line(len(self.choices))

    def set_choices(self, choices):
        self.choices = choices
        self.draw_choices()

    def set(self, title, choices):
        self.set_title(title)
        self.set_choices(choices)
