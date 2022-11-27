import os

import tidal
import tidal_helpers
import ecc108a
from esp32 import Partition

# sleep_sel just gets in the way of using lightsleep
tidal_helpers.esp_sleep_enable_gpio_switch(False)

# Initialize USB early on
tidal.usb.initialize()
tidal.init_lcd()
ecc108a.init()

if tidal.BUTTON_FRONT.value() == 0:
    # Boot to the recovery menu
    from bootmenu import BootMenu
    menu = BootMenu()
else:
    import emf_png
    import lodepng
    (w, h, buf) = lodepng.decode565(emf_png.DATA)
    tidal.display.blit_buffer(buf, 0, 0, w, h)

    from app_launcher import Launcher
    menu = Launcher()

try:
    os.mkdir("/apps")
except OSError:
    pass

# If we've made it to here, any OTA update has _probably_ gone ok...
Partition.mark_app_valid_cancel_rollback()

menu.main()
