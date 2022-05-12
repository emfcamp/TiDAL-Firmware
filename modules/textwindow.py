import tidal
import vga2_8x8 as default_font

class TextWindow:

    UP_ARROW = '\x18'
    DOWN_ARROW = '\x19'
    RIGHT_ARROW = '\x1A'
    LEFT_ARROW = '\x1B'

    def __init__(self, bg=None, fg=None, title=None, font=None, buttons=None):
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
        self.pos_y = 0
        self.display = tidal.display
        self.line_offset = None
        self.set_title(title, redraw=False)
        self.buttons = buttons

    def width(self):
        return self.display.width()

    def height(self):
        return self.display.height()

    def width_chars(self):
        return self.display.width() // self.font.WIDTH

    def height_chars(self):
        return self.display.height() // self.font.HEIGHT

    def line_height(self):
        if self.font.HEIGHT <= 8:
            return self.font.HEIGHT + 1
        else:
            # The larger fonts look fine without an extra pixel
            return self.font.HEIGHT

    def cls(self):
        """Clears entire screen, redraws title if there is one"""
        self.draw_title()
        self.clear_from_line(0)

    def redraw(self):
        """Subclasses which override this need to ensure every pixel in the window is drawn to
           (ie do not assume background is auto-cleared by anything).
        """
        self.cls()

    def clear_from_line(self, line=None):
        """Clears screen from line down"""
        if line is None:
            line = self.get_next_line()
        else:
            # Passing in a line also updates next_line
            self.set_next_line(line)
        y = self.get_line_pos(line)
        h = self.height() - (y - self.pos_y)
        self.display.fill_rect(0, y, self.width(), h, self.bg)

    def println(self, text="", y=None, fg=None, bg=None, centre=False):
        if y is None:
            y = self.current_line
            self.current_line = self.current_line + 1
        if bg is None:
            bg = self.bg
        if fg is None:
            fg = self.fg
        ypos = self.pos_y + self.line_offset + y * self.line_height()
        self.draw_line(text, ypos, fg, bg, centre)

    def draw_line(self, text, ypos, fg, bg, centre):
        text_width = len(text) * self.font.WIDTH
        w = self.width()
        if centre:
            xpos = (w - text_width) // 2
        else:
            xpos = (w - self.width_chars() * self.font.WIDTH) // 2
        self.display.fill_rect(0, ypos, w, self.line_height(), bg)
        self.draw_text(text, xpos, ypos, fg, bg)

    def draw_text(self, text, xpos, ypos, fg, bg):
        # Replace the non-ASCII £ with the correct encoding for vga font. Oh for
        # some proper codecs support, or even str.translate...
        text = text.encode().replace(b'\xC2\xA3', b'\x9C')

        self.display.text(self.font, text, xpos, ypos, fg, bg)

    def draw_title(self):
        if self.title:
            title_lines = self.title.split("\n")
            for i, line in enumerate(title_lines):
                self.draw_line(line, self.pos_y + i * self.line_height(), self.fg, self.bg, True)
            liney = self.pos_y + len(title_lines) * self.line_height()
            w = self.width()
            self.display.fill_rect(0, liney, w, 1, self.bg)
            self.display.hline(0, liney + 1, w, self.fg)
            self.display.fill_rect(0, liney + 2, w, 3, self.bg)

    def set_title(self, title, redraw=True):
        self.title = title
        prev_line_offset = self.line_offset
        if title is None:
            self.line_offset = 0
        else:
            self.line_offset = len(title.split("\n")) * self.line_height() + 5
        if redraw:
            if prev_line_offset is None or self.line_offset == prev_line_offset:
                self.draw_title()
            else:
                # A full redraw is needed if the height of the title has changed
                self.redraw()

    def set_next_line(self, next_line):
        self.current_line = next_line

    def get_next_line(self):
        return self.current_line

    def get_line_pos(self, line):
        return self.pos_y + self.line_offset + line * self.line_height()

    def get_max_lines(self):
        return (self.height() - self.line_offset) // self.line_height()

    def progress_bar(self, line, percentage, fg=None):
        """Display a line-sized progress bar for a percentage value 0-100"""
        if fg is None:
            fg = self.fg
        x = (self.width() - 100) // 2
        y = self.get_line_pos(line)
        self.display.fill_rect(x, y, percentage, self.font.HEIGHT, fg)
        # In case progress goes down, clear the right-hand side of the line
        self.display.fill_rect(x + percentage, y, self.width() - (x + percentage), self.font.HEIGHT, self.bg)

    def flow_lines(self, text):
        # Don't word wrap, just chop off
        lines = text.split("\n")
        result = []
        max_len = self.width_chars()
        for line in lines:
            line_len = len(line)
            i = 0
            while i < line_len:
                n = min(line_len - i, max_len)
                result.append(line[i:i+n])
                i = i + n

        if len(result) == 0:
            # Have to return at least one line
            result.append("")
        return result

class Menu(TextWindow):

    def __init__(self, bg, fg, focus_bg, focus_fg, title, choices, font=None, buttons=None):
        super().__init__(bg, fg, title, font, buttons)
        self.focus_fg = focus_fg
        self.focus_bg = focus_bg
        self.choices = choices
        self._focus_idx = 0
        self._top_idx = 0

    def draw_item(self, index, focus):
        text = self.choices[index][0]
        # The top and bottom items visible on screen should draw an arrow if there are more items not shown
        max_chars = self.width_chars() - 1
        if index == self._top_idx and self._top_idx > 0:
            text = text[0:max_chars] + (" " * (max_chars - len(text))) + self.UP_ARROW
        elif index == self._top_idx + self.get_max_lines() - 1 and len(self.choices) > index + 1:
            text = text[0:max_chars] + (" " * (max_chars - len(text))) + self.DOWN_ARROW

        fg = self.focus_fg if focus else self.fg
        bg = self.focus_bg if focus else self.bg

        self.println(text, index - self._top_idx, fg, bg)

    def focus_idx(self):
        return self._focus_idx

    @property
    def _end_idx(self):
        """One more than the bottom-most index shown on screen"""
        return self._top_idx + min(self.get_max_lines(), len(self.choices) - self._top_idx)

    def check_focus_visible(self):
        if self._focus_idx < self._top_idx:
            self._top_idx = self._focus_idx
            return True
        elif self._focus_idx >= self._top_idx + self.get_max_lines():
            self._top_idx = self._focus_idx - self.get_max_lines() + 1
            return True
        else:
            return False

    def set_focus_idx(self, i, redraw=True):
        prev_focus = self._focus_idx
        self._focus_idx = i % len(self.choices)
        needs_full_redraw = self.check_focus_visible()
        if needs_full_redraw:
            self.draw_items()
        elif redraw:
            self.draw_item(prev_focus, focus=False)
            self.draw_item(self._focus_idx, focus=True)

    def draw_items(self):
        for i in range(self._top_idx, self._end_idx):
            self.draw_item(i, i == self._focus_idx)
        self.clear_from_line(self._end_idx - self._top_idx)

    def redraw(self):
        self.draw_title()
        self.check_focus_visible()
        self.draw_items()

    def set_choices(self, choices, redraw=True):
        if choices is None:
            choices = ()
        self.choices = choices
        self._focus_idx = min(self._focus_idx, len(choices)) # Probably no point trying to preserve this?
        self.check_focus_visible()
        if redraw:
            self.draw_items()

    def set(self, title, choices, redraw=True):
        self.set_title(title, redraw)
        self.set_choices(choices, redraw)
