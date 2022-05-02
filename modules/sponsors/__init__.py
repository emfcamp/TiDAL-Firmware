import tidal
from textwindow import TextWindow
from app import PagedApp
from . import sponsor1_png
from . import sponsor2_png
from . import sponsor3_png

class ImageWindow(TextWindow):
    """Simple window class that just displays a single image, centred on screen"""
    def __init__(self, frozen_img):
        super().__init__(tidal.BLACK, tidal.BLUE)
        self.display = tidal.display
        self.img = frozen_img

    def redraw(self):
        self.cls()
        self.display.bitmap(self.img, (self.width() - self.img.WIDTH) // 2, (self.height() - self.img.HEIGHT) // 2)

class Sponsors(PagedApp):

    pages = (
        ImageWindow(sponsor1_png),
        ImageWindow(sponsor2_png),
        ImageWindow(sponsor3_png),
    )
