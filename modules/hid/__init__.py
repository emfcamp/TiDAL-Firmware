from textwindow import TextWindow
from app import App, task_coordinator
from tidal import *

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
            usb.hid.send_key()
            task_coordinator.context_changed("menu")


