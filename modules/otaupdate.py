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
    
    buttons = None
    started = False
    sync = False
    
    def run_sync(self):
        self.sync = True
        self.on_start()
        self.on_activate()
        self.sync = False # Reset in case we're subsequently re-run from Launcher

    def get_app_id(self):
        return "otaupdate"

    def check_for_interrupts(self):
        # Only needed once the app returns to the scheduler having completed
        return False

    def supports_rotation(self):
        return False

    def on_start(self):
        self.window = textwindow.TextWindow(MAGENTA, WHITE, "Firmware Update")

    def wait_for_a(self):
        while True:
            if BUTTON_A.value() == 0:
                return True
            elif BUTTON_FRONT.value() == 0:
                if not self.sync:
                    import scheduler
                    scheduler.get_scheduler().switch_app(None)
                return False
            time.sleep(0.1)

    def on_activate(self):
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

        if self.wait_for_a():
            window.clear_from_line(line)
            self.connect()

    def connect(self):
        window = self.window
        line = window.get_next_line()

        ssid = wifi.get_ssid()
        if not ssid:
            window.println("No WIFI config!")
            return

        if not wifi.status():
            wifi.connect()
            while True:
                window.println("Connecting to", line)
                window.println(f"{ssid}...", line + 1)
                if wifi.wait():
                    # Returning true means connected
                    break

                window.println("WiFi timed out", line)
                window.println("[A] to retry", line + 1)
                if not self.wait_for_a():
                    return

                if wifi.get_sta_status() == network.STAT_CONNECTING:
                    pass # go round loop and keep waiting
                else:
                    wifi.disconnect()
                    wifi.connect()

        window.println("IP:")
        window.println(wifi.get_ip())

        self.otaupdate()

    def otaupdate(self):
        window = self.window
        window.println()
        line = window.get_next_line()
        self.confirmed = False

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
                if not self.wait_for_a():
                    result = None
                    retry = False

        if result:
            window.println("Updated OK.")
            window.println("Press [A] to")
            window.println("reboot and")
            window.println("finish update.")
            self.wait_for_a()
            machine.reset()
        else:
            print("Update cancelled")

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
                if not self.wait_for_a():
                    print("Cancelling update")
                    return False

                # Clear confirmation text
                window.set_next_line(line)
            self.confirmed = True
            window.println("Updating...")
            window.println()

        window.progress_bar(window.get_next_line(), val)
        return True

    def on_deactivate(self):
        pass
