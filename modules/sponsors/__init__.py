import tidal
from textwindow import TextWindow
from app import PagedApp
from buttons import Buttons
import lodepng

from . import sponsored_by_png
from . import aiven_png
from . import ardc_png
from . import codethink_png
from . import google_png
from . import huboo_png
from . import iluli_png
from . import ingeniunda_png
from . import lucid_png
from . import mathworks_png
from . import mullvad_png
from . import onega_png
from . import ookla_png
from . import pcbgogo_png
from . import pimoroni_png
from . import pulsant_png
from . import sandcat_png
from . import sargasso_png
from . import secquest_png
from . import sos_png
from . import suborbital_png
from . import syndicate_systems_png
from . import the_at_company_png
from . import twilio_png
from . import uberspace_png
from . import ucl_png

SPONSORS = (
    syndicate_systems_png,
    pcbgogo_png,
    google_png,
    lucid_png,
    twilio_png,
    aiven_png,
    ardc_png,
    mathworks_png,
    sargasso_png,
    sos_png,
    huboo_png,
    iluli_png,
    mullvad_png,
    onega_png,
    ucl_png,
    codethink_png,
    ingeniunda_png,
    ookla_png,
    pulsant_png,
    sandcat_png,
    secquest_png,
    suborbital_png,
    the_at_company_png,
    uberspace_png,
    pimoroni_png,
)

class ImageWindow(TextWindow):
    """Simple window class that just displays a single image, centred on screen"""
    def __init__(self, frozen_img, buttons):
        super().__init__(tidal.WHITE, tidal.BLUE, None, None, buttons)
        self.display = tidal.display
        self.img = frozen_img

    def redraw(self):
        self.cls()
        (w, h, buf) = lodepng.decode565(self.img.DATA)
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2
        self.display.blit_buffer(buf, x, y, w, h)

class Sponsors(PagedApp):

    def __init__(self):
        super().__init__()
        # Normally switching pages would cancel any autorepeat on the left/right
        # buttons, sharing a common Buttons instance avoids that.
        shared_buttons = Buttons()
        shared_buttons.on_press(tidal.BUTTON_B, self.flip)
        pages = [sponsored_by_png]
        for img in SPONSORS:
            pages.append(ImageWindow(img, shared_buttons))
        self.pages = pages

    def supports_rotation(self):
        return True

    def on_activate(self):
        r = self.get_rotation()
        if r != 90 and r != 270:
            self.set_rotation(90, redraw=False)
        super().on_activate()
