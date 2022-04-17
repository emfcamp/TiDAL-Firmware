from tidal import *
import st7789
import vga1_8x8 as font
import esp32
import time

BG = st7789.BLUE
FG = st7789.WHITE
FOCUS_FG = st7789.BLACK
FOCUS_BG = st7789.CYAN

_current_line = 0

def cls():
    global _current_line
    display.fill(BG)
    _current_line = 0


def print_line(txt, y=None, fg=FG, bg=BG):
    global _current_line
    if y is None:
        y = _current_line
        _current_line = _current_line + 1

    dw = display.width()
    num_spaces = (dw // font.WIDTH) - len(txt)
    display.text(font, txt + (" " * num_spaces), 0, y * (font.HEIGHT + 1), fg, bg)


def web_repl():
    cls()
    print_line("--- Web REPL ---")

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

    print_line("SSID:")
    print_line(wifi_cfg.ssid)
    print_line("")
    print_line("Password: ")
    print_line(wifi_cfg.password)

    import esp
    esp.osdebug(None)
    import webrepl
    webrepl.start()


def usb_keyboard():
    cls()
    print_line("USB Keyboard")
    print_line("------------")
    print_line("Joystick maps to")
    print_line("cursor keys, A")
    print_line("and B are")
    print_line("themselves.")
    import _thread
    import joystick
    _thread.start_new_thread(joystick.joystick_active, ())


# Note, the text for each choice needs to be <= 16 characters in order to fit on screen
choices = [
    ("USB Keyboard", usb_keyboard),
    ("Web REPL", web_repl),
]

choices_y = 4 # Which line the choices start on

_focussed = 0

def focus_item(i):
    global _focussed
    print_line(choices[_focussed][0], choices_y + _focussed, FG, BG)
    _focussed = i % len(choices)
    print_line(choices[_focussed][0], choices_y + _focussed, FOCUS_FG, FOCUS_BG)


def show_boot_menu():
    print("Showing boot menu on LCD...")
    init_lcd()

    cls()
    print_line("   EMF 2022")
    print_line("TiDAL Boot Menu")
    print_line("-" * (display.width() // font.WIDTH))

    y = choices_y
    for (text, fn) in choices:
        print_line(text, y)
        y = y + 1
    focus_item(0)

    while True:
        if JOY_DOWN.value() == 0:
            focus_item(_focussed + 1)
        elif JOY_UP.value() == 0:
            focus_item(_focussed - 1)
        elif BUTTON_A.value() == 0 or BUTTON_B.value() == 0 or JOY_CENTRE.value() == 0:
            choices[_focussed][1]()
            return

        time.sleep(0.2)
