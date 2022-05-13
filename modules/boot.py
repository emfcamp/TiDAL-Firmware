import tidal
import tidal_helpers
from esp32 import Partition

# sleep_sel just gets in the way of using lightsleep
tidal_helpers.esp_sleep_enable_gpio_switch(False)

# Initialize USB early on
tidal.usb.initialize()
tidal.init_lcd()

if tidal.BUTTON_FRONT.value() == 0:
    # Boot to the recovery menu
    from bootmenu import BootMenu
    menu = BootMenu()
    menu.main()
else:
    from app_launcher import Launcher
    menu = Launcher()

import _thread
import tidal
_thread.stack_size(16 * 1024)
menu_thread = _thread.start_new_thread(menu.main, ())

# If we've made it to here, any OTA update has _probably_ gone ok...
Partition.mark_app_valid_cancel_rollback()

from term_menu import UartMenu
term_menu = UartMenu(gts=tidal.system_power_off, pm=None)
term_menu.main()

