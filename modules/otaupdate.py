from tidal import *
import buttons
from textwindow import TextWindow
import esp32
from esp32 import Partition
import network
import ota
import time

window = None
_confirmed = False

def main():
    global window
    window = TextWindow(MAGENTA, WHITE)
    window.println("OTA Update")
    window.println("----------")
    window.println()

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

    buttons.on_press(BUTTON_A, connect)
    buttons.poll()

def connect(_):
    buttons.clear_callbacks()

    # Clear prompt
    line = window.get_next_line()
    window.println("", line)
    window.println("", line + 1)

    try:
        import wifi_cfg
        window.println("Connecting...", line)
        # Give WIFI chance to get IP address
        for retry in range(0, 10):
            stat = wifi_cfg.sta.status()
            if stat == network.STAT_CONNECTING:
                time.sleep(1.0)
            else:
                break

        if wifi_cfg.sta.status() != network.STAT_GOT_IP:
            window.println("Not connected!")
            return
        window.println("IP: {}".format(wifi_cfg.sta.ifconfig()[0]))
    except Exception as e:
        print(e)
        window.println("No WIFI config!")
        return

    update()

def update():
    window.println()
    window.println("Checking...", window.get_next_line())

    try:
        result = ota.update(progress)
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

def progress(version, val):
    global _confirmed
    if not _confirmed:
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
        _confirmed = True
        window.println("Updating...")
        window.println()

    y = window.get_next_line() * (window.font.HEIGHT + 1)
    display.fill_rect((window.width() - 100) // 2, y, val, window.font.HEIGHT, WHITE)
    return True
