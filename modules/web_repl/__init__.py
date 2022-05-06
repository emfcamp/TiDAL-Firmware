from app import TextApp
from scheduler import get_scheduler
import wifi

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

        if not wifi.is_configured_sta() and not wifi.get_ssid():
            settings.set("wifi_ssid", "tidal")
            settings.set("wifi_password", "tidal")
            settings.set("wifi_ap", True)
            settings.save()

    def on_activate(self):
        super().on_activate()
        window = self.window
        window.cls()
        # TODO does webrepl work when not in AP mode?
        if wifi.is_configured_sta():
            window.println("WIFI not in")
            window.println("AP mode!")
        else:
            if not wifi.isuporconnected():
                wifi.configure_interface()
            window.println("SSID:")
            window.println(wifi.get_ssid())
            window.println("Password: ")
            window.println(wifi.get_password())

        get_scheduler().set_sleep_enabled(False)

        import esp
        esp.osdebug(None)
        import webrepl
        webrepl.start()
