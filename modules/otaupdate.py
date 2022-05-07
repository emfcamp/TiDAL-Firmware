from tidal import *
import textwindow
from esp32 import Partition
import machine
import network
import ota
import time
import wifi

# Note, this intentionally doesn't inherit App or TextApp to limit dependencies
# because it is on the critical path from the Recovery Menu.
# But it acts sufficiently like it does, to satisfy the app launcher
class OtaUpdate:
    
    title = "Firmware Update"
    buttons = None
    started = False
    
    BG = MAGENTA
    FG = WHITE

    confirmed = False

    def run_sync(self):
        self.on_start()
        self.on_activate()

    def get_app_id(self):
        return "otaupdate"

    def check_for_interrupts(self):
        # Only needed once the app returns to the scheduler having completed
        return False

    def on_start(self):
        self.window = textwindow.TextWindow(self.BG, self.FG, self.title)

    def on_activate(self):
        set_display_rotation(0)
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

        if not wifi.is_configured_sta():
            window.println("No WIFI config!")
            return

        if not wifi.isconnected():
            window.println("Connecting...", line)
            wifi.connect()

            while True:
                window.clear_from_line(line)
                # Give WIFI chance to get IP address
                for retry in range(0, 15):
                    stat = wifi.status()
                    if stat == network.STAT_CONNECTING:
                        time.sleep(1.0)
                    else:
                        break

                if wifi.status() == network.STAT_GOT_IP:
                    break
                else:
                    window.println("WiFi timed out", line)
                    window.println("[A] to retry", line + 1)
                    while BUTTON_A.value() == 1:
                        time.sleep(0.2)
                
        window.println("IP:")
        window.println(wifi.get_ip())

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
            window.println("Press [A] to")
            window.println("reboot and")
            window.println("finish update.")
            while BUTTON_A.value() == 1:
                time.sleep(0.2)
            machine.reset()
        # else update was cancelled

    def progress(self, version, val):
        window = self.window
        if not self.confirmed:
            if len(version) > 0:
                if version == ota.get_version():
                    window.println("No new version")
                    window.println("available.")
                    return False

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

        window.progress_bar(window.get_next_line(), val)
        return True
