import tidal
import vga2_8x8 as default_font

class TextWindow:

    UP_ARROW = '\x18'
    DOWN_ARROW = '\x19'
    RIGHT_ARROW = '\x1A'
    LEFT_ARROW = '\x1B'

    DEFAULT_BG = tidal.color565(0, 0, 0x60)
    DEFAULT_FG = tidal.WHITE

    def __init__(self, bg=None, fg=None, title=None, font=None, buttons=None):
        if bg is None:
            bg = self.DEFAULT_BG
        if fg is None:
            fg = self.DEFAULT_FG
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

    def width_chars(self, font=None):
        return self.display.width() // (font or self.font).WIDTH

    def height_chars(self, font=None):
        return self.display.height() // (font or self.font).HEIGHT

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

    def draw_text(self, text, xpos, ypos, fg, bg, font=None):
        btext = to_cp437(text)
        self.display.text(font or self.font, btext, xpos, ypos, fg, bg)

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

    def flow_lines(self, text, font=None):
        # Don't word wrap, just chop off
        lines = text.split("\n")
        result = []
        max_len = self.width_chars(font)
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

    DEFAULT_FOCUS_FG = tidal.BLACK
    DEFAULT_FOCUS_BG = tidal.CYAN

    def __init__(self, bg, fg, focus_bg, focus_fg, title, choices, font=None, buttons=None):
        super().__init__(bg, fg, title, font, buttons)
        if focus_fg is None:
            focus_fg = self.DEFAULT_FOCUS_FG
        if focus_bg is None:
            focus_bg = self.DEFAULT_FOCUS_BG
        self.focus_fg = focus_fg
        self.focus_bg = focus_bg
        self.choices = choices
        self._focus_idx = 0
        self._top_idx = 0
        if buttons:
            buttons.on_press(tidal.JOY_DOWN, lambda: self.set_focus_idx(self.focus_idx() + 1))
            buttons.on_press(tidal.JOY_UP, lambda: self.set_focus_idx(self.focus_idx() - 1))
            # For rotation to work, interrupts have to be active on all direction buttons even if just a no-op
            buttons.on_press(tidal.JOY_LEFT, lambda: None)
            buttons.on_press(tidal.JOY_RIGHT, lambda: None)
            def select():
                if len(self.choices):
                    self.choices[self.focus_idx()][1]()
            buttons.on_press(tidal.JOY_CENTRE, select, autorepeat=False)
            buttons.on_press(tidal.BUTTON_A, select, autorepeat=False)

    def draw_item(self, index, focus):
        text = self.choices[index][0]
        # The top and bottom items visible on screen should draw an arrow if there are more items not shown
        max_chars = self.width_chars() - 1
        if index == self._top_idx and self._top_idx > 0:
            text = text[0:max_chars] + (" " * (max_chars - len(text))) + self.UP_ARROW
        elif index == self._top_idx + self.get_max_items() - 1 and len(self.choices) > index + 1:
            text = text[0:max_chars] + (" " * (max_chars - len(text))) + self.DOWN_ARROW

        fg = self.focus_fg if focus else self.fg
        bg = self.focus_bg if focus else self.bg

        self.println(text, index - self._top_idx, fg, bg)

    def focus_idx(self):
        return self._focus_idx

    @property
    def _end_idx(self):
        """One more than the bottom-most index shown on screen"""
        return self._top_idx + min(self.get_max_items(), len(self.choices) - self._top_idx)

    def get_max_items(self):
        return self.get_max_lines()

    def check_focus_visible(self):
        # Returns true if things needed to be scrolled
        max_items = self.get_max_items()
        if self._focus_idx < self._top_idx:
            self._top_idx = self._focus_idx
            return True
        elif self._focus_idx >= self._top_idx + max_items:
            self._top_idx = self._focus_idx - max_items + 1
            return True
        else:
            return False

    def set_focus_idx(self, i, redraw=True):
        prev_focus = self._focus_idx
        self._focus_idx = i % len(self.choices)
        needs_full_redraw = redraw and self.check_focus_visible()
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


_cp437 = {
    "Ç": b'\x80',
    "ü": b'\x81',
    "é": b'\x82',
    "â": b'\x83',
    "ä": b'\x84',
    "à": b'\x85',
    "å": b'\x86',
    "ç": b'\x87',
    "ê": b'\x88',
    "ë": b'\x89',
    "è": b'\x8A',
    "ï": b'\x8B',
    "î": b'\x8C',
    "ì": b'\x8D',
    "Ä": b'\x8E',
    "Å": b'\x8F',
    "É": b'\x90',
    "æ": b'\x91',
    "Æ": b'\x92',
    "ô": b'\x93',
    "ö": b'\x94',
    "ò": b'\x95',
    "û": b'\x96',
    "ù": b'\x97',
    "ÿ": b'\x98',
    "Ö": b'\x99',
    "Ü": b'\x9A',
    "¢": b'\x9B',
    "£": b'\x9C',
    "¥": b'\x9D',
    "₧": b'\x9E',
    "ƒ": b'\x9F',
    "á": b'\xA0',
    "í": b'\xA1',
    "ó": b'\xA2',
    "ú": b'\xA3',
    "ñ": b'\xA4',
    "Ñ": b'\xA5',
    "ª": b'\xA6',
    "º": b'\xA7',
    "¿": b'\xA8',
    "⌐": b'\xA9',
    "¬": b'\xAA',
    "½": b'\xAB',
    "¼": b'\xAC',
    "¡": b'\xAD',
    "«": b'\xAE',
    "»": b'\xAF',
    "ß": b'\xE1', # This is actually beta, but looks sufficently like sharp s
    "€": b'\xEE', # This is actually epsilon, but looks sufficiently like euro
    "≡": b'\xF0',
    "±": b'\xF1',
    "≥": b'\xF2',
    "≤": b'\xF3',
    "⌠": b'\xF4',
    "⌡": b'\xF5',
    "÷": b'\xF6',
    "≈": b'\xF7',
    "°": b'\xF8',
    "∙": b'\xF9',
    "·": b'\xFA',
    "√": b'\xFB',
    "ⁿ": b'\xFC',
    "²": b'\xFD',
    "■": b'\xFE',
}

def to_cp437(text):
    if len(text) == 0:
        # micropy is doing something dodgy with bytes(bytearray()) such that
        # it's not null terminated whereas everything else accessible with
        # mp_obj_str_get_str(), including bytes(), is. So shortcirtuit to avoid
        # that.
        return bytes()

    result = bytearray()
    for ch in text:
        if b := _cp437.get(ch):
            result += b
        else:
            result += ch.encode()
    # Of course returning a bytearray here messes up as it's not implictly
    # castable to a char* in mp_obj_str_get_str, but bytes is...
    return bytes(result)
