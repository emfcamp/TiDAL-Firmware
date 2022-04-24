from tidal import *
from buttons import Buttons
from app import TextApp
from esp32 import Partition
import network
import ota
import time

class OtaUpdate(TextApp):
    
    app_id = "otaupdate"
    title = "Firmware Update"
    
    BG = MAGENTA
    FG = WHITE

    confirmed = False

    def on_start(self):
        super().on_start()
        self.buttons.clear_callbacks() # Don't support BUTTON_FRONT for now
        window = self.window
        window.cls()

        try:
            current = Partition(Partition.RUNNING)
            nxt = current.get_next_update()
        except:
            # Hitting this likely means your partition table is out of date or
            # you're missing ota_data_initial.bin
            window.println("No OTA info!")
            window.println("USB flash needed")
            return

        window.println("Boot: " + current.info()[4])
        window.println("Next: " + nxt.info()[4])
        window.println("Version:")
        window.println(ota.get_version())
        window.println()
        line = window.get_next_line()
        window.println("Press [A] to")
        window.println("check updates.")
        window.set_next_line(line)

        self.buttons.on_press(BUTTON_A, lambda p: self.connect())

    def connect(self):
        self.buttons.clear_callbacks()

        # Clear prompt
        window = self.window
        line = window.get_next_line()
        window.println("", line)
        window.println("", line + 1)

        try:
            import wifi_cfg
            window.println("Connecting...", line)
            # Give WIFI chance to get IP address
            for retry in range(0, 15):
                stat = wifi_cfg.sta.status()
                if stat == network.STAT_CONNECTING:
                    time.sleep(1.0)
                else:
                    break

            if wifi_cfg.sta.status() != network.STAT_GOT_IP:
                window.println("WiFi timed out")
                return
            window.println("IP:")
            window.println(wifi_cfg.sta.ifconfig()[0])
        except Exception as e:
            print(e)
            window.println("No WIFI config!")
            return

        self.otaupdate()

    def otaupdate(self):
        window = self.window
        window.println()
        window.println("Checking...", window.get_next_line())

        try:
            result = ota.update(lambda version, val: self.progress(version, val))
        except OSError as e:
            print("Error:" + str(e))
            window.println("Update failed!")
            window.println("Error {}".format(e.errno))
            return

        if result:
            window.println("Updated OK.")
            window.println("Power cycle to")
            window.println("finish update.")
        else:
            window.println("Update cancelled")

    def progress(self, version, val):
        window = self.window
        if not self.confirmed:
            if len(version) > 0:
                window.println("New version:")
                window.println(version)
                window.println()
                line = window.get_next_line()
                window.println("Press [A] to")
                window.println("confirm update.")
                while BUTTON_A.value() == 1:
                    time.sleep(0.2)
                # Clear confirmation text
                window.set_next_line(line)
            self.confirmed = True
            window.println("Updating...")
            window.println()

        y = window.get_line_pos(window.get_next_line())
        window.display.fill_rect((window.width() - 100) // 2, y, val, window.font.HEIGHT, WHITE)
        return True
