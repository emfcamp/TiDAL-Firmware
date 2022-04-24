from app import TextApp
from tidal import *
import joystick

class USBKeyboard(TextApp):
    app_id = "keyboard"
    title = "USB Keyboard"

    def __init__(self):
        super().__init__()
        self.pressed = set()

    def on_start(self):
        super().on_start()
        self.buttons.on_up_down(BUTTON_A, lambda pin, down: self.send_key(joystick.HID_KEY_A, down))
        self.buttons.on_up_down(BUTTON_B, lambda pin, down: self.send_key(joystick.HID_KEY_B, down))
        self.buttons.on_up_down(JOY_DOWN, lambda pin, down: self.send_key(joystick.HID_KEY_ARROW_DOWN, down))
        self.buttons.on_up_down(JOY_UP, lambda pin, down: self.send_key(joystick.HID_KEY_ARROW_UP, down))
        self.buttons.on_up_down(JOY_LEFT, lambda pin, down: self.send_key(joystick.HID_KEY_ARROW_LEFT, down))
        self.buttons.on_up_down(JOY_RIGHT, lambda pin, down: self.send_key(joystick.HID_KEY_ARROW_RIGHT, down))
        self.buttons.on_up_down(JOY_CENTRE, lambda pin, down: self.send_key(joystick.HID_KEY_ENTER, down))

    def on_wake(self):
        super().on_wake()
        window = self.window
        window.cls()
        window.println("Joystick maps to")
        window.println("cursor keys, A")
        window.println("and B are")
        window.println("themselves.")

    def send_key(self, k, down):
        if down:
            self.pressed.add(k)
        else:
            self.pressed.discard(k)

        usb.hid.send_key(*self.pressed)
