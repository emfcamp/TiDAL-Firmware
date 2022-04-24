import st7789
import tidal
from textwindow import Menu
from app import App


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


class BootMenu(Menu, App):

    app_id = "menu"
    title = "Emergency Menu"

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

    def on_wake(self):
        self.cls()

    def update(self):
        if tidal.JOY_DOWN.value() == 0:
            self.focus_idx += 1
        elif tidal.JOY_UP.value() == 0:
            self.focus_idx -= 1
        elif any((
                tidal.BUTTON_A.value() == 0,
                tidal.BUTTON_B.value() == 0,
                tidal.JOY_CENTRE.value() == 0,
            )):
            with open("lastbootitem.txt", "wt", encoding="ascii") as f:
                f.write(str(self.focus_idx))
            self.choices[self.focus_idx][1]()
