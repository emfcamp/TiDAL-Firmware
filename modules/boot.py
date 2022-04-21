import _thread
import emf_png
import tidal
import time
from bootmenu import show_boot_menu

# Initialize USB early on
tidal.usb.initialize()
tidal.init_lcd()

tidal.display.bitmap(emf_png, 0, 0)
time.sleep(0.5)


# TODO: figure out how to get show_boot_menu to use callbacks and become async
# so it needn't be wrapped in a thread to prevent it blocking the serial/USB
# REPL.
_thread.start_new_thread(show_boot_menu, ())
