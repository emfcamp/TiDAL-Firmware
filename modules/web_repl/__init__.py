from app import App, task_coordinator
from textwindow import TextWindow
from tidal import BUTTON_FRONT

class WebRepl(App, TextWindow):

    def on_start(self):
        try:
            with open("webrepl_cfg.py") as f:
                pass
        except OSError:
            # No webrepl password is set, use tilda
            with open("webrepl_cfg.py", "wt", encoding="utf-8") as cfg:
                cfg.write("PASS = 'tilda'\n")

        try:
            with open("wifi_cfg.py") as f:
                pass
        except OSError:
            # No wifi config, use tilda/tilda
            with open("wifi_cfg.py", "wt", encoding="utf-8") as cfg:
                cfg.write("""
import network

ssid = "tilda"
password = "tilda"

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password)
""")


    def on_wake(self):
        self.cls()
        self.println("--- Web REPL ---")
        import wifi_cfg

        self.println("SSID:")
        self.println(getattr(wifi_cfg, "ssid", "?"))
        self.println("")
        self.println("Password: ")
        self.println(getattr(wifi_cfg, "password", "?"))

        import esp
        esp.osdebug(None)
        import webrepl
        webrepl.start()

    def update(self):
        if BUTTON_FRONT.value() == 0:
            import webrepl
            webrepl.stop()
            task_coordinator.context_changed("menu")
