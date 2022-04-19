from tidal import *
import tidal
from textwindow import TextWindow, Menu
from app import App, main_task
import torch
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


class USBKeyboard(TextWindow, App):
    app_id = "keyboard"
    
    thread_running = False

    def on_wake(self):
        self.cls()
        self.println("USB Keyboard")
        self.println("------------")
        self.println("Joystick maps to")
        self.println("cursor keys, A")
        self.println("and B are")
        self.println("themselves.")

        if not self.thread_running:
            #import _thread
            #
            #_thread.start_new_thread(joystick.joystick_active, ())
            self.thread_running = True
    
    
    def update(self):
        pressed = []
        import joystick
        if BUTTON_A.value() == 0:
            pressed.append(joystick.HID_KEY_A)
        if BUTTON_B.value() == 0:
            pressed.append(joystick.HID_KEY_B)
        if JOY_DOWN.value() == 0:
            pressed.append(joystick.HID_KEY_ARROW_DOWN)
        if JOY_UP.value() == 0:
            pressed.append(joystick.HID_KEY_ARROW_UP)
        if JOY_LEFT.value() == 0:
            pressed.append(joystick.HID_KEY_ARROW_LEFT)
        if JOY_RIGHT.value() == 0:
            pressed.append(joystick.HID_KEY_ARROW_RIGHT)
        if JOY_CENTRE.value() == 0:
            pressed.append(joystick.HID_KEY_ENTER)
        
        # Allow a maximum of 6 scancodes
        pressed = pressed[:6]
        usb.hid.send_key(*pressed)
        
        if pressed == [joystick.HID_KEY_A, joystick.HID_KEY_B]:
            main_task.contextChanged("menu")
            usb.hid.send_key()



class BootMenu(Menu, App):

    app_id = "menu"

    # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
    choices = (
        ({"text": "USB Keyboard"}, lambda: main_task.contextChanged("keyboard")),
        ({"text": "Web REPL"}, web_repl),
        ({"text": "Torch"}, lambda: main_task.contextChanged("torch")),
    )

    def on_wake(self):
        self.cls()

    def update(self):
        if tidal.JOY_DOWN.value() == 0:
            self.focus_idx += 1
        elif tidal.JOY_UP.value() == 0:
            self.focus_idx -= 1
        elif any((
                tidal.BUTTON_A.value() == 0,
                tidal.BUTTON_B.value() == 0,
                tidal.JOY_CENTRE.value() == 0,
            )):
            with open("lastbootitem.txt", "wt", encoding="ascii") as f:
                f.write(str(self.focus_idx))
            self.choices[self.focus_idx][1]()
