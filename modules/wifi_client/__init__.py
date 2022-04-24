from tidal import *
import network
from textwindow import Menu
from app import App, task_coordinator


class WifiClient(Menu, App):
    
    app_id = "wifi_client"
    title = "WiFi Networks"
    interval = 0.2
    
    BG = st7789.GREEN
    FG = st7789.BLACK
    FOCUS_FG = st7789.BLACK
    FOCUS_BG = st7789.WHITE

    @property
    def title(self):
        title = "WiFi Networks"
        
        if not hasattr(self, "sta"):
            # Not yet loaded interface
            return title
        
        ip = self.sta.ifconfig()[0]
        
        if ssid := self.get_wifi_ssid():
            title += "\n" + ssid
        title += "\n" + self.get_wifi_status()
        if ip != "0.0.0.0":
            title += "\n" + ip
        return title

    def get_wifi_ssid(self):
        return self.sta.config("essid")

    def get_wifi_status(self):
        status = self.sta.status()
        if status == network.STAT_IDLE:
            return "Disconnected"
        elif status == network.STAT_CONNECTING:
            return "Connecting"
        elif status == network.STAT_GOT_IP:
            self.connecting = False
            return "Connected"
        else:
            return "Error"

    def join_selected(self):
        print(f"Id {self.focus_idx}")
        print(f"Net {self.wifi_networks[self.focus_idx]}")
        
        return self.join_wifi(self.wifi_networks[self.focus_idx][0])

    def join_wifi(self, ssid):
        print(f"Joining {ssid}")
        ssid = ssid.decode("latin-1")
        self.connecting = True
        self.sta.disconnect()
        wifi_cfg = f"""
import network

sta = network.WLAN(network.STA_IF)
sta.active(True)
ssid = "{ssid}"
sta.connect(ssid)
"""
        with open("wifi_cfg.py", "wt", encoding="utf-8") as wifi_cfg_file:
            wifi_cfg_file.write(wifi_cfg)
        self.sta.connect(ssid)

    @property
    def choices(self):
        return [
            ({"text": wifi[0]}, self.join_selected)
            for wifi in self.wifi_networks
        ] + [
            ({"text": "Refresh..."}, self.refresh)
        ]

    def refresh(self):
        self.sta = network.WLAN(network.STA_IF)
        self.sta.active(True)
        self.wifi_networks = [
            network
            for network in self.sta.scan()
            if network[4] == 0 and network[0]
        ]
        self.cls()

    def on_start(self):
        self.wifi_networks = []
        self.connecting = False
        self.i = 0

    def on_wake(self):
        self.cls()

    def update(self):
        if self.connecting:
            self.i += 1
            if self.i > 5:
                self.cls()
                self.i = 0
        if BUTTON_FRONT.value() == 0:
            task_coordinator.context_changed("menu")
        elif JOY_DOWN.value() == 0:
            self.focus_idx += 1
        elif JOY_UP.value() == 0:
            self.focus_idx -= 1
        elif any((
                BUTTON_A.value() == 0,
                BUTTON_B.value() == 0,
                JOY_CENTRE.value() == 0,
            )):
            self.choices[self.focus_idx][1]()
