from tidal import *
from textwindow import TextWindow
import esp32
import time

BG = BLUE
FG = WHITE
FOCUS_FG = BLACK
FOCUS_BG = CYAN

window = None

def web_repl():
    window.cls()
    window.println("--- Web REPL ---")

    try:
        with open("webrepl_cfg.py") as f:
            pass
    except OSError:
        # No webrepl password is set, use tilda
        with open("webrepl_cfg.py", "wt", encoding="utf-8") as cfg:
            cfg.write("PASS = 'tilda'\n")

    try:
        with open("wifi_cfg.py") as f:
            pass
    except OSError:
        # No wifi config, use tilda/tilda
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

    window.println("SSID:")
    window.println(wifi_cfg.ssid)
    window.println("")
    window.println("Password: ")
    window.println(wifi_cfg.password)

    import esp
    esp.osdebug(None)
    import webrepl
    webrepl.start()


def usb_keyboard():
    window.cls()
    window.println("USB Keyboard")
    window.println("------------")
    window.println("Joystick maps to")
    window.println("cursor keys, A")
    window.println("and B are")
    window.println("themselves.")
    import _thread
    import joystick
    _thread.start_new_thread(joystick.joystick_active, ())

def run_torch():
    import torch
    torch.main()

def run_emflogo():
    import emflogo
    emflogo.main()

# Note, the text for each choice needs to be <= 16 characters in order to fit on screen
choices = [
    ("USB Keyboard", usb_keyboard),
    ("Web REPL", web_repl),
    ("Torch", run_torch),
    ("EMF Logo", run_emflogo),
]

choices_y = 4 # Which line the choices start on

_focussed = 0

def focus_item(i):
    global _focussed
    window.println(choices[_focussed][0], choices_y + _focussed, FG, BG)
    _focussed = i % len(choices)
    window.println(choices[_focussed][0], choices_y + _focussed, FOCUS_FG, FOCUS_BG)


def show_boot_menu():
    global window
    print("Showing boot menu on LCD...")
    init_lcd()
    window = TextWindow(BG, FG)

    window.println("EMF 2022", centre=True)
    window.println("TiDAL Boot Menu")
    window.println("-" * (window.width() // window.font.WIDTH))

    y = choices_y
    for (text, fn) in choices:
        window.println(text, y)
        y = y + 1

    initial_item = 0
    try:
        with open("lastbootitem.txt") as f:
            initial_item = int(f.read())
    except:
        pass
    if initial_item < 0 or initial_item >= len(choices):
        initial_item = 0
    focus_item(initial_item)

    while True:
        if JOY_DOWN.value() == 0:
            focus_item(_focussed + 1)
        elif JOY_UP.value() == 0:
            focus_item(_focussed - 1)
        elif BUTTON_A.value() == 0 or BUTTON_B.value() == 0 or JOY_CENTRE.value() == 0:
            with open("lastbootitem.txt", "w") as f:
                f.write(str(_focussed))
            choices[_focussed][1]()
            return

        time.sleep(0.2)
