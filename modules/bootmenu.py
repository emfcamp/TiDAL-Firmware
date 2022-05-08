from tidal import *
import textwindow
import time

def run_applauncher():
    import app_launcher
    app = app_launcher.Launcher()
    app.run_sync()

def run_applauncher_nosleep():
    from scheduler import get_scheduler
    get_scheduler().set_sleep_enabled(False)
    run_applauncher()

def run_otaupdate():
    import otaupdate
    app = otaupdate.OtaUpdate()
    app.run_sync()

def erase_storage():
    from esp32 import Partition
    MP_BLOCKDEV_IOCTL_BLOCK_ERASE = 6

    window = textwindow.TextWindow(RED, WHITE, "Erase storage")
    window.cls()
    window.println("Press [A] to")
    window.println("erase VFS")
    window.println("partition.")
    window.println()
    window.println("BE VERY SURE")
    window.println("ABOUT THIS!")
    while True:
        if BUTTON_A.value() == 0:
            break
        time.sleep(0.2)
    window.clear_from_line(0)
    window.println()

    partitions = Partition.find(type=Partition.TYPE_DATA, subtype=0x81)
    if len(partitions) != 1:
        window.println("VFS Partition")
        window.println("not found!")
        return

    vfs_partition = partitions[0]
    num_blocks = vfs_partition.info()[3] // 4096
    percent = -1
    window.println("Erasing...")
    line = window.get_next_line()
    for i in range(0, num_blocks):
        new_percent = (i * 100) // num_blocks
        if new_percent > percent:
            percent = new_percent
            window.progress_bar(line, percent)
        vfs_partition.ioctl(MP_BLOCKDEV_IOCTL_BLOCK_ERASE, i)
    window.clear_from_line(line - 1)
    window.println("Erase complete")


# Note, this is a minimal app definition that does not rely on IRQs, timers or uasyncio working
# For consistency, it is structured to look similar to a MenuApp even though it doesn't actually
# derive from it.
class BootMenu:

    TITLE = "Recovery Menu"
    BG = RED
    FG = WHITE
    FOCUS_FG = RED
    FOCUS_BG = WHITE

    # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
    CHOICES = (
        ("App Launcher", run_applauncher),
        ("Nosleep Launcher", run_applauncher_nosleep),
        ("Firmware Update", run_otaupdate),
        ("Erase storage",  erase_storage),
        ("Power off (UVLO)", system_power_off),
    )

    def main(self):
        print("Showing Recovery Menu")
        window = textwindow.Menu(self.BG, self.FG, self.FOCUS_BG, self.FOCUS_FG, self.TITLE, self.CHOICES)
        window.redraw()
        while True:
            if JOY_DOWN.value() == 0:
                window.set_focus_idx(window.focus_idx() + 1)
            elif JOY_UP.value() == 0:
                window.set_focus_idx(window.focus_idx() - 1)
            elif JOY_CENTRE.value() == 0:
                window.choices[window.focus_idx()][1]()
                break
            time.sleep(0.2)
