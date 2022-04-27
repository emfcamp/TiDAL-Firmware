import emf_png
import tidal
import app
import time
import tidal_helpers
from esp32 import Partition

# sleep_sel just gets in the way of using lightsleep
tidal_helpers.esp_sleep_enable_gpio_switch(False)

# Initialize USB early on
tidal.usb.initialize()
tidal.init_lcd()

tidal.display.bitmap(emf_png, 0, 0)
time.sleep(0.5)

if tidal.JOY_DOWN.value() == 0:
    # This is an emergency boot
    from bootmenu import BootMenu

    menu = BootMenu()
    Partition.mark_app_valid_cancel_rollback()
    menu.run_sync()
else:
    from app_launcher import Launcher
    import uasyncio

    menu = Launcher()
    
    # If we've made it to here, any OTA update has _probably_ gone ok...
    Partition.mark_app_valid_cancel_rollback()

    async def main():
        menu_task = uasyncio.create_task(menu.run())
        app.task_coordinator.context_changed("menu")
        await menu_task
    uasyncio.run(main())

    

# TODO: figure out how to get show_boot_menu to use callbacks and become async
# so it needn't be wrapped in a thread to prevent it blocking the serial/USB
# REPL.
menu = BootMenu()
