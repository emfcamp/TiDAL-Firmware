import tidal
from textwindow import TextWindow
from buttons import Buttons

class Keyboard(TextWindow):

    KEYS = (
        "1234567890-=",
        "qwertyuiop[]",
        "asdfghjkl;'#",
       "\\zxcvbnm,./\n",
        " "
    )

    SHIFTED_KEYS = (
        "!@£$%^&*()_+",
        "QWERTYUIOP{}",
        'ASDFGHJKL:"~',
        "|ZXCVBNM<>?\n",
        " "
    )

    MOD_KEYS = (
        "¡€.....°..±≈",
        "èéêëùúûüìíîï",
        "àáâäåßòóôö«»",
        "`ÅÄç..ñÑ≤≥¿\n",
        " "
    )

    KEY_SETS = (KEYS, SHIFTED_KEYS, MOD_KEYS)

    ROW_OFFSETS = (1, 1, 1, 1, 34)

    def __init__(self, completion_callback, prompt=None, initial_value="", multiline_allowed=False):
        buttons = Buttons()
        super().__init__(tidal.BLACK, tidal.WHITE, None, None, buttons)
        self.keyset = 0
        self.last_keyset_used = 0
        self.x = 0
        self.y = 0
        self.completion_callback = completion_callback
        buttons.on_press(tidal.JOY_LEFT, lambda : self.set_xy(self.x - 1, self.y))
        buttons.on_press(tidal.JOY_RIGHT, lambda : self.set_xy(self.x + 1, self.y))
        buttons.on_press(tidal.JOY_UP, lambda : self.set_xy(self.x, self.y - 1))
        buttons.on_press(tidal.JOY_DOWN, lambda : self.set_xy(self.x, self.y + 1))
        buttons.on_press(tidal.JOY_CENTRE, self.click, autorepeat=False)
        buttons.on_press(tidal.BUTTON_A, self.switch_keyset, autorepeat=False)
        buttons.on_press(tidal.BUTTON_B, self.backspace)
        buttons.on_press(tidal.BUTTON_FRONT, self.back_button, autorepeat=False)
        self.multiline_allowed = multiline_allowed
        self.num_text_lines = 1
        self.set(prompt, initial_value)

    @property
    def key_width(self):
        return 3 + self.font.WIDTH
    
    @property
    def key_height(self):
        return 3 + self.font.HEIGHT

    @property
    def keys(self):
        return self.KEY_SETS[self.keyset]
    
    def height(self):
        return self.line_offset + ((self.num_text_lines + 2) * self.line_height()) + len(self.KEYS) * self.key_height + 1

    def draw_key(self, x, y, focussed):
        w = self.width()
        key_width = self.key_width
        xoff = (w - (12 * key_width)) // 2
        k = self.keys[y][x]
        if k == " ":
            key_width = 6 * key_width
        key_height = self.key_height
        xpos = xoff + self.ROW_OFFSETS[y] + x * key_width
        ypos = self.get_line_pos(self.num_text_lines + 1) + y * key_height
        if focussed:
            fg = self.bg
            bg = self.fg
        else:
            fg = self.fg
            bg = self.bg
        boxcol = tidal.color565(128, 128, 128)
        self.display.rect(xpos, ypos, key_width + 1, key_height + 1, boxcol)
        if k == " ":
            # Space bar is bigger, draw it with a fill_rect instead
            self.display.fill_rect(xpos + 1, ypos + 1, key_width - 1, key_height - 1, bg)
        elif k == "\n":
            # There's no glyph in the font we use for a enter key - instead use
            # left-pointing-arrow and draw an extra bit.
            self.display.rect(xpos + 1, ypos + 1, key_width - 1, key_height - 1, bg)
            self.display.text(self.font, self.LEFT_ARROW, xpos + 2, ypos + 2, fg, bg)
            self.display.vline(xpos + 8, ypos + 2, 4, fg)
        else:
            self.display.rect(xpos + 1, ypos + 1, key_width - 1, key_height - 1, bg)
            self.draw_text(k, xpos + 2, ypos + 2, fg, bg)

        # Draw leading/trailing background if necessary
        if y > 0:
            # Don't nuke bottom pixel of row above
            ypos += 1
            key_height -= 1
        if x == 0:
            # First key, fill preceding gap
            if xoff + self.ROW_OFFSETS[y] > 0:
                self.display.fill_rect(0, ypos, xoff + self.ROW_OFFSETS[y], key_height + 1, self.bg)
        if x + 1 == len(self.keys[y]):
            # Last key, fill end gap
            xpos += key_width + 1
            self.display.fill_rect(xpos, ypos, w - xpos, key_height + 1, self.bg)

    def redraw(self):
        self.draw_title()
        self.draw_textarea()
        self.draw_keys()

        xoff = (self.width() - (12 * self.key_width)) // 2
        ypos = self.get_line_pos(self.num_text_lines + 1) + len(self.KEYS) * self.key_height + 1
        col = tidal.color565(128, 128, 128)
        self.display.fill_rect(0, ypos, self.width(), self.line_height(), self.bg)
        self.draw_text("B=bksp A=shift", xoff, ypos + 1, col, self.bg)

    def draw_textarea(self):
        lines = self.flow_lines(self.text)
        for (i, line) in enumerate(lines):
            self.println(line, i)
        i = len(lines)
        while i < self.num_text_lines:
            self.println("", i)
            i += 1
        self.println("", i)

    def draw_keys(self):
        keys = self.keys
        for y in range(len(keys)):
            row = keys[y]
            for x in range(len(row)):
                self.draw_key(x, y, x == self.x and y == self.y)

    def switch_keyset(self):
        if self.keyset and self.last_keyset_used == self.keyset:
            self.keyset = 0
        else:
            self.keyset = (self.keyset + 1) % len(self.KEY_SETS)
        self.draw_keys()

    def set_xy(self, x, y):
        self.draw_key(self.x, self.y, False)
        self.y = y % len(self.KEYS)
        self.x = x % len(self.KEYS[self.y])
        self.draw_key(self.x, self.y, True)

    def click(self):
        k = self.keys[self.y][self.x]
        if not self.multiline_allowed and k == "\n":
            self.completion_callback(self.text)
        else:
            self.last_keyset_used = self.keyset
            self.set_text(self.text + k, redraw=True)

    def backspace(self):
        self.text = self.text[:-1]
        self.draw_textarea()

    def back_button(self):
        self.completion_callback(self.text)

    def set(self, prompt, text, redraw=False):
        self.x = 0
        self.y = 0
        self.set_title(prompt, redraw=redraw)
        self.pos_y = self.display.height() - self.height()
        self.set_text(text, redraw=redraw)

    def set_text(self, text, redraw=False):
        if text is None:
            text = ""
        self.text = text
        new_line_count = len(self.flow_lines(self.text))
        if new_line_count > self.num_text_lines:
            self.num_text_lines = new_line_count
            self.pos_y = self.display.height() - self.height()
            if redraw:
                self.redraw()
        elif redraw:
            self.draw_textarea()
