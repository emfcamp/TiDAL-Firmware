# st7789_passthrough.py Driver for ST7789 LCD displays using the ST7789 C driver for nano-gui

import framebuf
import gc
import micropython
import uasyncio as asyncio
import st7789
from boolpalette import BoolPalette
from tidal import display as tidal_display

@micropython.viper
def _lcopy(dest:ptr16, source:ptr8, lut:ptr16, length:int):
    # rgb565 - 16bit/pixel
    n = 0
    for x in range(length):
        c = source[x]
        dest[n] = lut[c >> 4]  # current pixel
        n += 1
        dest[n] = lut[c & 0x0f]  # next pixel
        n += 1

class ST7789Passthrough(framebuf.FrameBuffer):

    lut = bytearray(0xFF for _ in range(32))  # set all colors to BLACK

    # Convert r, g, b in range 0-255 to a 16 bit colour value rgb565.
    # LS byte goes into LUT offset 0, MS byte into offset 1
    # Same mapping in linebuf so LS byte is shifted out 1st
    # @staticmethod
    def rgb(r, g, b):
        return ((b & 0xf8) << 5 | (g & 0x1c) << 11 | (g & 0xe0) >> 5 | (r & 0xf8))

    def __init__(self):
        height = 240
        width = 135
        self.height = height  # Required by Writer class
        self.width = width
        self._lock = asyncio.Lock()
        mode = framebuf.GS4_HMSB  # Use 4bit greyscale.
        self.palette = BoolPalette(mode)
        gc.collect()
        buf = bytearray(height * -(-width // 2))  # Ceiling division for odd widths
        self._mvb = memoryview(buf)
        super().__init__(buf, width, height, mode)
        self._linebuf = bytearray(self.width * 2)  # 16 bit color out
        # It is useful (but not essential) to call show() here. Without it, the
        # user gets no indication that a ugui app is loading for the first time,
        # which takes a considerable length of time.
        self.show()

    #@micropython.native # Made virtually no difference to timing.
    def show(self):
        clut = ST7789Passthrough.lut
        wd = -(-self.width // 2)  # Ceiling division for odd number widths
        end = self.height * wd
        lb = memoryview(self._linebuf)
        buf = self._mvb
        for start in range(0, end, wd):
            _lcopy(lb, buf[start:], clut, wd)  # Copy and map colors
            tidal_display.blit_buffer(lb, 0, start//wd, self.width, 1)

    # Asynchronous refresh with support for reducing blocking time.
    async def do_refresh(self, split=5):
        async with self._lock:
            lines, mod = divmod(self.height, split)  # Lines per segment
            if mod:
                raise ValueError('Invalid do_refresh arg.')
            clut = ST7789Passthrough.lut
            wd = -(-self.width // 2)
            lb = memoryview(self._linebuf)
            buf = self._mvb
            line = 0
            for n in range(split):
                for start in range(wd * line, wd * (line + lines), wd):
                    _lcopy(lb, buf[start :], clut, wd)  # Copy and map colors
                    tidal_display.blit_buffer(lb, 0, line, self.width, 1)
                    line += 1
                await asyncio.sleep(0)
