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
        self.cls()


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
