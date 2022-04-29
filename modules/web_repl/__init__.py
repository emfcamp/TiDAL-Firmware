from app import TextApp
from scheduler import get_scheduler

class WebRepl(TextApp):

    title = "Web REPL"

    def on_start(self):
        super().on_start()
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

    def on_activate(self):
        super().on_activate()
        window = self.window
        window.cls()
        import wifi_cfg

        window.println("SSID:")
        window.println(getattr(wifi_cfg, "ssid", "?"))
        window.println("")
        window.println("Password: ")
        window.println(getattr(wifi_cfg, "password", "?"))
        get_scheduler().set_sleep_enabled(False)

        import esp
        esp.osdebug(None)
        import webrepl
        webrepl.start()
