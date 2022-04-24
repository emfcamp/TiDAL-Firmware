from tidal import *
from buttons import Buttons
from textwindow import TextWindow
from app import App
from esp32 import Partition
import network
import ota
import time

class OtaUpdate(TextWindow, App):
    
    app_id = "otaupdate"
    interval = 0.2
    
    BG = MAGENTA
    FG = WHITE

    confirmed = False

    def on_start(self):
        self.cls()
        self.println("OTA Update")
        self.println("----------")
        self.println()

        try:
            current = Partition(Partition.RUNNING)
            nxt = current.get_next_update()
        except:
            # Hitting this likely means your partition table is out of date or
            # you're missing ota_data_initial.bin
            self.println("No OTA info!")
            self.println("USB flash needed")
            return

        self.println("Boot: " + current.info()[4])
        self.println("Next: " + nxt.info()[4])
        self.println("Version:")
        self.println(ota.get_version())
        self.println()
        line = self.get_next_line()
        self.println("Press [A] to")
        self.println("check updates.")
        self.set_next_line(line)

        self.buttons = Buttons()
        self.buttons.on_press(BUTTON_A, lambda p: self.connect())

    def update(self):
        self.buttons.poll()

    def connect(self):
        self.buttons.clear_callbacks()

        # Clear prompt
        line = self.get_next_line()
        self.println("", line)
        self.println("", line + 1)

        try:
            import wifi_cfg
            self.println("Connecting...", line)
            # Give WIFI chance to get IP address
            for retry in range(0, 10):
                stat = wifi_cfg.sta.status()
                if stat == network.STAT_CONNECTING:
                    time.sleep(1.0)
                else:
                    break

            if wifi_cfg.sta.status() != network.STAT_GOT_IP:
                self.println("Not connected!")
                return
            self.println("IP: {}".format(wifi_cfg.sta.ifconfig()[0]))
        except Exception as e:
            print(e)
            self.println("No WIFI config!")
            return

        self.otaupdate()

    def otaupdate(self):
        self.println()
        self.println("Checking...", self.get_next_line())

        try:
            result = ota.update(lambda version, val: self.progress(version, val))
        except OSError as e:
            print("Error:" + str(e))
            self.println("Update failed!")
            self.println("Error {}".format(e.errno))
            return

        if result:
            self.println("Updated OK.")
            self.println("Power cycle to")
            self.println("finish update.")
        else:
            self.println("Update cancelled")

    def progress(self, version, val):
        if not self.confirmed:
            if len(version) > 0:
                self.println("New version:")
                self.println(version)
                self.println()
                line = self.get_next_line()
                self.println("Press [A] to")
                self.println("confirm update.")
                while BUTTON_A.value() == 1:
                    time.sleep(0.2)
                # Clear confirmation text
                self.set_next_line(line)
            self.confirmed = True
            self.println("Updating...")
            self.println()

        y = self.get_next_line() * (self.font.HEIGHT + 1)
        display.fill_rect((self.width() - 100) // 2, y, val, self.font.HEIGHT, WHITE)
        return True
