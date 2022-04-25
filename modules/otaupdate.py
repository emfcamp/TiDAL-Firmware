from tidal import *
import textwindow
from esp32 import Partition
import network
import ota
import time

# Note, this intentionally doesn't inherit App or TextApp to limit dependencies
# as this is on the critical path from the Recovery Menu.
# But it acts sufficiently like it does, to satisfy the app launcher
class OtaUpdate:
    
    app_id = "otaupdate"
    title = "Firmware Update"
    
    BG = MAGENTA
    FG = WHITE

    confirmed = False

    def run_sync(self):
        self.on_start()
        self.on_wake()

    def on_start(self):
        self.window = textwindow.TextWindow(self.BG, self.FG, self.title)

    def on_wake(self):
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

        while BUTTON_A.value() == 1:
            time.sleep(0.2)

        window.clear_from_line(line)
        self.connect()

    def connect(self):
        window = self.window
        line = window.get_next_line()

        try:
            import wifi_cfg
            wifi_cfg.sta.status()
        except Exception as e:
            print(e)
            window.println("No WIFI config!")
            return

        while True:
            window.clear_from_line(line)
            window.println("Connecting...", line)
            # Give WIFI chance to get IP address
            for retry in range(0, 15):
                stat = wifi_cfg.sta.status()
                if stat == network.STAT_CONNECTING:
                    time.sleep(1.0)
                else:
                    break

            if wifi_cfg.sta.status() == network.STAT_GOT_IP:
                break
            else:
                window.println("WiFi timed out", line)
                window.println("[A] to retry", line + 1)
                while BUTTON_A.value() == 1:
                    time.sleep(0.2)
                
        window.println("IP:")
        window.println(wifi_cfg.sta.ifconfig()[0])

        self.otaupdate()

    def otaupdate(self):
        window = self.window
        window.println()
        line = window.get_next_line()

        retry = True
        while retry:
            window.clear_from_line(line)
            window.println("Checking...", line)

            try:
                result = ota.update(lambda version, val: self.progress(version, val))
                retry = False
            except OSError as e:
                print("Error:" + str(e))
                window.println("Update failed!")
                window.println("Error {}".format(e.errno))
                window.println("[A] to retry")
                while BUTTON_A.value() == 1:
                    time.sleep(0.2)

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
