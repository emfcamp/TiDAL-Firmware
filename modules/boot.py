import tidal
import tidal_helpers
from esp32 import Partition

# sleep_sel just gets in the way of using lightsleep
tidal_helpers.esp_sleep_enable_gpio_switch(False)

# Initialize USB early on
tidal_helpers.inhibit_sleep()
tidal.usb.initialize()
tidal.init_lcd()

if tidal.BUTTON_FRONT.value() == 0:
    # Boot to the recovery menu
    from bootmenu import BootMenu
    menu = BootMenu()
else:
    from app_launcher import Launcher
    menu = Launcher()

# If we've made it to here, any OTA update has _probably_ gone ok...
Partition.mark_app_valid_cancel_rollback()

menu.main()
