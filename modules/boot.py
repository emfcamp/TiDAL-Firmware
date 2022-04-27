import tidal
import ota

# Initialize USB early on
tidal.usb.initialize()
ota.gpio_hold(14, False)
tidal.init_lcd()

from textwindow import TextWindow
import machine
win = TextWindow(tidal.WHITE, tidal.BLACK)
tidal.display.fill(tidal.WHITE)
win.println("Deepsleep test")
win.println("10 seconds...")
ota.gpio_hold(14, True)
machine.deepsleep(10000)
