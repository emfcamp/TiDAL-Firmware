import _thread
import joystick

_thread.start_new_thread(joystick.joystick_active, ())

try:
    open("webrepl_cfg.py")
except OSError:
    # No webrepl password is set, use aaaa
    with open("webrepl_cfg.py", "wt", encoding="utf-8") as cfg:
        cfg.write("PASS = 'tilda'\n")
        

try:
    open("wifi_cfg.py")
except OSError:
    # No webrepl password is set, use aaaa
    with open("wifi_cfg.py", "wt", encoding="utf-8") as cfg:
        cfg.write("""
import network

ssid = "tilda"
password = "tilda"

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid, password=password)
""")


import wifi_cfg

import esp
esp.osdebug(None)
import webrepl
webrepl.start()
