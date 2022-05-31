import tidal
from textwindow import TextWindow
from app import PagedApp
from buttons import Buttons
import lodepng
import settings
from scheduler import get_scheduler

SPONSORS = (
    "syndicate_systems_png",
    "pcbgogo_png",
    "espressif_png",
    "google_png",
    "lucid_png",
    "twilio_png",
    "aiven_png",
    "ardc_png",
    "mathworks_png",
    "sargasso_png",
    "sos_png",
    "huboo_png",
    "iluli_png",
    "mullvad_png",
    "onega_png",
    "ucl_png",
    "codethink_png",
    "ingeniunda_png",
    "ookla_png",
    "pulsant_png",
    "sandcat_png",
    "secquest_png",
    "suborbital_png",
    "the_at_company_png",
    "uberspace_png",
    "pimoroni_png",
)

SLIDESHOW_INTERVAL = 1500

class ImageWindow(TextWindow):
    """Simple window class that just displays a single image, centred on screen"""
    def __init__(self, frozen_img_name, buttons, bg=tidal.WHITE):
        super().__init__(bg, TextWindow.DEFAULT_BG, None, None, buttons)
        self.display = tidal.display
        self.img_name = frozen_img_name
        self.img = None

    def redraw(self):
        if not self.img:
            self.img = getattr(__import__("sponsors."+self.img_name), self.img_name)
        (w, h, buf) = lodepng.decode565(self.img.DATA)
        self.cls()
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
        shared_buttons.on_press(tidal.JOY_CENTRE, self.toggle_animate)
        pages = [ImageWindow("sponsored_by_png", shared_buttons, bg=None)]
        for img in SPONSORS:
            pages.append(ImageWindow(img, shared_buttons))
        self.pages = pages
        self.timer = None
        self.entry_orientation = None

    def supports_rotation(self):
        return True

    def on_start(self):
        super().on_start()
        self.buttons.on_press(tidal.BUTTON_FRONT, self.navigate_back_if_not_firstrun, autorepeat=False)

    def on_activate(self):
        r = self.get_rotation()
        if r != 90 and r != 270:
            self.entry_orientation = r
            self.set_rotation(270, redraw=False)
        super().on_activate()

        self.timer = self.periodic(SLIDESHOW_INTERVAL, lambda: self.set_page(self.page + 1))

    def on_deactivate(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
        if self.entry_orientation is not None:
            self.set_rotation(self.entry_orientation, redraw=False)
            self.entry_orientation = None
        super().on_deactivate()

    def is_firstrun(self):
        return not settings.get("first_run_done", False)

    def set_page(self, val, redraw=True):
        # Since this is called from a timer, make sure the screen doesn't sleep while we're slideshowing!
        get_scheduler().reset_inactivity()
        if val % len(self.pages) == 0 and self.is_firstrun():
            settings.set("first_run_done", True)
            settings.save()
            super().set_page(0, redraw=False)
            self.pages[0].cls()
            get_scheduler().switch_app(None)
            self.timer.cancel()
            self.timer = None
        else:
            super().set_page(val, redraw)

    def toggle_animate(self):
        x = self.window.width() - 8
        y = 1
        self.window.display.fill_rect(x - 2, y, 10, 10, tidal.WHITE)
        if self.timer:
            self.timer.cancel()
            self.timer = None
            self.window.display.fill_rect(x, y, 2, 7, tidal.BLACK)
            self.window.display.fill_rect(x + 4, y, 2, 7, tidal.BLACK)
        else:
            self.window.draw_text("\x10", x, y, tidal.BLACK, tidal.WHITE) # Play triangle
            self.timer = self.periodic(SLIDESHOW_INTERVAL, lambda: self.set_page(self.page + 1))

    def navigate_back_if_not_firstrun(self):
        if not self.is_firstrun():
            self.navigate_back()
