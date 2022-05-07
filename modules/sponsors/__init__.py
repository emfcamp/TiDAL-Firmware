import tidal
from textwindow import TextWindow
from app import PagedApp
from buttons import Buttons
from . import sponsor1_png
from . import sponsor2_png
from . import sponsor3_png

class ImageWindow(TextWindow):
    """Simple window class that just displays a single image, centred on screen"""
    def __init__(self, frozen_img, buttons):
        super().__init__(tidal.BLACK, tidal.BLUE, None, None, buttons)
        self.display = tidal.display
        self.img = frozen_img

    def redraw(self):
        self.cls()
        self.display.bitmap(self.img, (self.width() - self.img.WIDTH) // 2, (self.height() - self.img.HEIGHT) // 2)

class Sponsors(PagedApp):

    def __init__(self):
        super().__init__()
        # Normally switching pages would cancel any autorepeat on the left/right
        # buttons, sharing a common Buttons instance avoids that.
        shared_buttons = Buttons()
        self.pages = (
            ImageWindow(sponsor1_png, shared_buttons),
            ImageWindow(sponsor2_png, shared_buttons),
            ImageWindow(sponsor3_png, shared_buttons),
        )

    def on_activate(self):
        # ST7789 does _not_ like trying to render images larger than the screen
        # in its current rotation... So for now given we have portrait
        # placeholder data, force the rotation.
        self.set_rotation(0, redraw=False)
        super().on_activate()
