import st7789
import tidal
from textwindow import Menu
from app import MenuApp


def web_repl():
    import web_repl
    app = web_repl.WebRepl()
    app.run_sync()

def hid():
    import hid
    app = hid.USBKeyboard()
    app.run_sync()

def torch():
    import torch
    app = torch.Torch()
    app.run_sync()

def run_otaupdate():
    import otaupdate
    app = otaupdate.OtaUpdate()
    app.run_sync()


class BootMenu(MenuApp):

    app_id = "menu"
    title = "Recovery Menu"

    BG = st7789.RED
    FG = st7789.WHITE
    FOCUS_FG = st7789.RED
    FOCUS_BG = st7789.WHITE

    # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
    choices = (
        ({"text": "USB Keyboard"}, hid),
        ({"text": "Web REPL"}, web_repl),
        ({"text": "Torch"}, torch),
        ({"text": "Firmware Update"}, run_otaupdate),
    )
