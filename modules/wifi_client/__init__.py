from tidal import *
import network
import settings
import wifi
from app import MenuApp
from scheduler import get_scheduler

class WifiClient(MenuApp):
    
    FOCUS_FG = BLACK
    FOCUS_BG = CYAN
    DEFAULT_TITLE = "Wi-Fi Config"
    NUM_RETRIES = 5

    choices = ()

    def update_ui(self, redraw=True):
        choices = []
        title = self.DEFAULT_TITLE
        if self.ssid:
            title += f"\n{self.ssid}"
            if wifi.is_ap():
                title += " (AP)"
            if wifi.isuporconnected():
                title += f"\n{wifi.get_ip()}"
            else:
                title += "\nNot connected"
                choices.append(("Connect", lambda: self.join_wifi(self.ssid, wifi.get_password())))
        elif self.wifi_networks:
            for (ssid, _) in self.wifi_networks:
                choices.append((ssid, self.join_selected))
        else:
            title += "\nNo SSID set"

        choices.append(("Scan...", self.scan))
        # choices.append(("Hidden SSID...", self.connect_hidden_ssid))
        self.window.set(title, choices, redraw=redraw)

    def scan(self):
        self.ssid = None
        self.window.set_choices(None)
        self.window.set_title(self.DEFAULT_TITLE)
        self.window.println("Scanning...", 0)
        self.window.clear_from_line(1)
        self.wifi_networks = []
        for ap in network.WLAN(network.STA_IF).scan():
            print(f"Found {ap}")
            if ap[0]:
                pass_required = ap[4] != 0
                try:
                    self.wifi_networks.append((ap[0].decode("utf-8"), pass_required))
                except:
                    # Ignore any APs that don't decode as valid UTF-8
                    pass
        self.update_ui()

    def on_start(self):
        super().on_start()
        get_scheduler().set_sleep_enabled(False)
        wifi.configure_interface()
        self.ssid = wifi.get_ssid()
        self.wifi_networks = []
        self.connection_timer = None

    def on_activate(self):
        self.update_ui(redraw=False)
        super().on_activate()

    def on_deactivate(self):
        if self.connection_timer:
            self.connection_timer.cancel()
            self.connection_timer = None

    def get_wifi_status(self):
        status = wifi.status()
        if status == network.STAT_IDLE:
            return "Disconnected"
        elif status == network.STAT_CONNECTING:
            return "Connecting"
        elif status == network.STAT_GOT_IP:
            self.connecting = False
            return f"IP: {wifi.get_ip()}"
        elif status == network.STAT_WRONG_PASSWORD:
            return "Bad password"
        else:
            return "Error"

    def join_selected(self):
        (ssid, password_required) = self.wifi_networks[self.window.focus_idx()]
        password = None
        if password_required:
            if ssid == "badge":
                # Special case for EMF
                password = "badge"
            else:
                password = self.keyboard_prompt("Enter password:")
                # print(f"Got password {password}")
        return self.join_wifi(self.wifi_networks[self.window.focus_idx()][0], password)

    def join_wifi(self, ssid, password):
        self.window.set_choices(None)
        self.window.println("Connecting...", 0)
        self.ssid = ssid
        wifi.connect(ssid, password)
        self.connection_timer = self.periodic(1000, self.update_connection)

    def cancel_timer(self):
        if self.connection_timer:
            self.connection_timer.cancel()
            self.connection_timer = None

    def update_connection(self):
        print(self.get_wifi_status())
        status = wifi.status()
        if status == network.STAT_CONNECTING:
            return

        if status == network.STAT_GOT_IP:
            wifi.save_settings()
        else:
            self.ssid = None

        self.cancel_timer()
        self.update_ui()
