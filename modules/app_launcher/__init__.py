import tidal
from app import MenuApp
from scheduler import get_scheduler
import emf_png

SPLASHSCREEN_TIME = 300 # ms

class Launcher(MenuApp):

    app_id = "menu"
    title = "EMF 2022 - TiDAL\nBoot Menu"
    BG = tidal.BLUE
    FG = tidal.WHITE
    FOCUS_FG = tidal.BLACK
    FOCUS_BG = tidal.CYAN

    @property
    def choices(self):
        # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
        return (
            ({"text": "USB Keyboard"}, lambda: self.launch("hid", "USBKeyboard")),
            ({"text": "Web REPL"}, lambda: self.launch("web_repl", "WebRepl")),
            ({"text": "Torch"}, lambda: self.launch("torch", "Torch")),
            ({"text": "Logo"}, lambda: self.launch("emflogo", "EMFLogo")),
            ({"text": "Update Firmware"}, lambda: self.launch("otaupdate", "OtaUpdate")),
        )
    
    # Boot entry point
    def main(self):
        get_scheduler().main(self)

    def __init__(self):
        super().__init__()
        self._apps = {}
        self.show_splash = True

    def on_activate(self):
        if self.show_splash and SPLASHSCREEN_TIME:
            # Don't call super, we don't want MenuApp to call cls yet
            self.buttons.deactivate() # Don't respond to buttons until after splashscreen dismissed
            tidal.display.bitmap(emf_png, 0, 0)
            self.after(SPLASHSCREEN_TIME, lambda: self.dismiss_splash())
        else:
            super().on_activate()

    def dismiss_splash(self):
        self.show_splash = False
        self.buttons.activate()
        self.window.cls()

    def launch(self, module_name, app_name):
        app = self._apps.get(app_name)
        if app is None:
            print(f"Creating app {app_name}...")
            module = __import__(module_name)
            app = getattr(module, app_name)()
            self._apps[app_name] = app
        get_scheduler().switch_app(app)
