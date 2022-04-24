import tidal
from esp32 import Partition

# Initialize USB early on
tidal.usb.initialize()
tidal.init_lcd()

if tidal.JOY_DOWN.value() == 0:
    # Boot to the recovery menu
    from bootmenu import BootMenu

    menu = BootMenu()
    Partition.mark_app_valid_cancel_rollback()
    menu.run_sync()
else:
    import app
    import time
    import emf_png
    from app_launcher import Launcher
    import uasyncio

    tidal.display.bitmap(emf_png, 0, 0)
    time.sleep(0.5)

    menu = Launcher()
    
    # If we've made it to here, any OTA update has _probably_ gone ok...
    Partition.mark_app_valid_cancel_rollback()

    async def main():
        menu_task = uasyncio.create_task(menu.run())
        app.task_coordinator.context_changed("menu")
        await menu_task
    uasyncio.run(main())
