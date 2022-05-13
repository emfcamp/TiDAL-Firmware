import tidal
import tidal_helpers
from app import MenuApp
from scheduler import get_scheduler
import emf_png

SPLASHSCREEN_TIME = 300 # ms

class Launcher(MenuApp):

    APP_ID = "menu"
    TITLE = "EMF 2022 - TiDAL\nBoot Menu"
    BG = tidal.BLUE
    FG = tidal.WHITE
    FOCUS_FG = tidal.BLACK
    FOCUS_BG = tidal.CYAN

    @property
    def choices(self):
        # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
        return (
            ("USB Keyboard", lambda: self.launch("hid", "USBKeyboard")),
            ("Name Badge", lambda: self.launch("hello", "Hello")),
            # ("Web REPL", lambda: self.launch("web_repl", "WebRepl")),
            ("Torch", lambda: self.launch("torch", "Torch")),
            ("Logo", lambda: self.launch("emflogo", "EMFLogo")),
            ("Update Firmware", lambda: self.launch("otaupdate", "OtaUpdate")),
            ("Wi-Fi Config", lambda: self.launch("wifi_client", "WifiClient")),
            ("Sponsors", lambda: self.launch("sponsors", "Sponsors")),
            ("Battery", lambda: self.launch("battery", "Battery")),
        )
    
    # Boot entry point
    def main(self):
        get_scheduler().main(self)

    def __init__(self):
        super().__init__()
        self._apps = {}
        self.show_splash = True

    def on_start(self):
        super().on_start()
        self.window.set_choices(self.choices, redraw=False)
        self.buttons.on_up_down(tidal.CHARGE_DET, self.charge_state_changed)
        self.buttons.on_press(tidal.BUTTON_FRONT, lambda: self.update_title(redraw=True))

        initial_item = 0
        try:
            with open("/lastapplaunch.txt") as f:
                initial_item = int(f.read())
        except:
            pass
        self.window.set_focus_idx(initial_item, redraw=False)

    def on_activate(self):
        if self.show_splash and SPLASHSCREEN_TIME:
            # Don't call super, we don't want MenuApp to call cls yet
            self.buttons.deactivate() # Don't respond to buttons until after splashscreen dismissed
            tidal.display.bitmap(emf_png, 0, 0)
            self.after(SPLASHSCREEN_TIME, lambda: self.dismiss_splash())
        else:
            self.update_title(redraw=False)
            super().on_activate()

    def dismiss_splash(self):
        self.show_splash = False
        self.on_activate()

    def update_title(self, redraw):
        title = self.TITLE
        if not get_scheduler().is_sleep_enabled():
            title += "\nSLEEP DISABLED"
        pwr = tidal.CHARGE_DET.value() == 0 and 1 or 0
        conn = tidal_helpers.usb_connected() and 1 or 0
        if pwr or conn:
            title += f"\nUSB pwr={pwr} conn={conn}"
        if title != self.window.title:
            self.window.set_title(title, redraw=redraw)

    def launch(self, module_name, app_name):
        app = self._apps.get(app_name)
        if app is None:
            print(f"Creating app {app_name}...")
            module = __import__(module_name)
            app = getattr(module, app_name)()
            self._apps[app_name] = app
        with open("/lastapplaunch.txt", "w") as f:
            f.write(str(self.window.focus_idx()))
        get_scheduler().switch_app(app)

    def charge_state_changed(self, charging):
        if not self.show_splash:
            self.update_title(redraw=True)
        get_scheduler().usb_plug_event(charging)
