from tidal import *
import textwindow
import time

def torch():
    import torch
    app = torch.Torch()
    app.run_sync()

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
    window.println()

    partitions = Partition.find(type=Partition.TYPE_DATA, subtype=0x81)
    if len(partitions) != 1:
        window.println("VFS Partition")
        window.println("not found!")
        return

    vfs_partition = partitions[0]
    num_blocks = vfs_partition.info()[3] // 4096
    percent = -1
    for i in range(0, num_blocks):
        new_percent = (i * 100) // num_blocks
        if new_percent > percent:
            percent = new_percent
            window.println("Erasing... {}%".format(percent), window.get_next_line())
        vfs_partition.ioctl(MP_BLOCKDEV_IOCTL_BLOCK_ERASE, i)
    window.println("Erase complete")

# Note, this is a minimal app definition that does not rely on IRQs, timers or uasyncio working
class BootMenu:

    title = "Recovery Menu"
    BG = RED
    FG = WHITE
    FOCUS_FG = RED
    FOCUS_BG = WHITE

    # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
    choices = (
        ({"text": "Firmware Update"}, run_otaupdate),
        ({"text": "Erase storage"},  erase_storage),
        ({"text": "Torch"}, torch),
    )

    def run_sync(self):
        print("Showing Recovery Menu")
        window = textwindow.Menu(self.BG, self.FG, self.FOCUS_BG, self.FOCUS_FG, self.title, self.choices)
        window.cls()
        while True:
            if JOY_DOWN.value() == 0:
                window.set_focus_idx(window.focus_idx() + 1)
            elif JOY_UP.value() == 0:
                window.set_focus_idx(window.focus_idx() - 1)
            elif JOY_CENTRE.value() == 0:
                self.choices[window.focus_idx()][1]()
                break
            time.sleep(0.2)
