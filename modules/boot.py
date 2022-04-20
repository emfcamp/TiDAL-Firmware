import _thread
import uasyncio

import tidal
import app
from bootmenu import BootMenu, USBKeyboard

# Initialize USB early on
tidal.usb.initialize()
tidal.init_lcd()

# TODO: figure out how to get show_boot_menu to use callbacks and become async
# so it needn't be wrapped in a thread to prevent it blocking the serial/USB
# REPL.
menu = BootMenu()
#_thread.start_new_thread(menu.run, ())

async def main():
    menu_task = uasyncio.create_task(menu.run())
    keyboard_task = uasyncio.create_task(USBKeyboard().run())
    app.task_coordinator.context_changed("menu")
    await uasyncio.gather(
        menu_task,
        keyboard_task
    )

uasyncio.run(main())
