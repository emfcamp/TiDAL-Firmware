import tidal
import tidal_helpers
from scheduler import get_scheduler
import uasyncio

# Only one Buttons object can be active at a time - whichever most recently
# called activate() gets the interrupts.
_current = None

def _button_irq(pin):
    if _current:
        _current._isr_flag = True

def _num(pin):
    return tidal_helpers.pin_number(pin)

_l = _num(tidal.JOY_LEFT)
_r = _num(tidal.JOY_RIGHT)
_u = _num(tidal.JOY_UP)
_d = _num(tidal.JOY_DOWN)

# When rotated 180 degrees, the JOY_UP GPIO should send callbacks to the callback registered for JOY_DOWN, etc
_rotations = {
    0: { _l: _l, _r: _r, _u: _u, _d: _d },
    90: { _l: _u, _r: _d, _u: _r, _d: _l },
    180: { _l: _r, _r: _l, _u: _d, _d: _u },
    270: { _l: _d, _r: _u, _u: _l, _d: _r },
}

class Button:
    def __init__(self, pin, callback, updown, autorepeat):
        self.pin = pin
        self.pin_number = _num(pin)
        self.callback = callback
        self.real_callback = None
        self.updown = updown
        self.autorepeat = autorepeat
        self.state = pin.value()

    def should_autorepeat(self):
        return (not self.updown) and self.autorepeat and (self.state == 0)

class Buttons:

    autorepeat_delay_time = 200 # ms
    autorepeat_time = 200 # ms

    def __init__(self):
        self._callbacks = {} # pin_number -> Button
        self._autorepeat_timer = None
        self._autorepeating_button = None
        self._isr_flag = False
        self._rotation = tidal.get_display_rotation()
        # This doesn't seem like the best place to put this, but I can't think of a better offhand
        self.on_up_down(tidal.CHARGE_DET, get_scheduler().usb_plug_event)

    def is_active(self):
        return _current == self

    def on_press(self, pin, callback, autorepeat=True):
        if autorepeat is True:
            autorepeat = self.autorepeat_time
        self._register_button(Button(pin, callback, False, autorepeat))

    def on_up_down(self, pin, callback):
        self._register_button(Button(pin, callback, True, False))

    def _register_button(self, button):
        k = button.pin_number
        if button.callback:
            self._callbacks[k] = button
            if self.is_active():
                self._register_irq(button)
        elif self._is_registered(button):
            del self._callbacks[k]
            if self.is_active():
                # print(f"Unregistering {button.pin}")
                tidal_helpers.set_lightsleep_irq(button.pin, None, None)

    def _is_registered(self, button):
        return button.pin_number in self._callbacks

    def get_callback(self, pin):
        if button := self._callbacks.get(_num(pin), None):
            return button.callback
        else:
            return None

    def _register_irq(self, button):
        while True:
            button.state = button.pin.value()
            level = 1 if button.state == 0 else 0
            # print(f"Registering {button.pin} for {level}")
            tidal_helpers.set_lightsleep_irq(button.pin, level, _button_irq)
            # And check we didn't just miss a transition
            if button.state == button.pin.value():
                break
            # else go round again

    def check_for_interrupts(self):
        if self._isr_flag:
            self._isr_flag = False
            uasyncio.create_task(self.check_buttons())
            return True
        else:
            return False

    async def check_buttons(self):
        # print("Checking buttons...")
        button_changed_state = False
        for button in self._callbacks.values():
            new_state = button.pin.value()
            valid = True
            if new_state != button.state:
                button_changed_state = True
                # print(f"{button.pin} state changed to {new_state}")
                button.state = new_state
                if button.updown:
                    self._send_callback_for_button(button.pin_number, button.state == 0)
                elif button.state == 0:
                    # Button pressed down
                    # button.callback()
                    self._send_callback_for_button(button.pin_number)

            # Check that we're still active and the button is still registered
            # (any callback we may have made above might've changed that), and
            # if so, reenable the interrupt if it's been fired (which is
            # indicated by handler being None).
            valid = self.is_active() and self._is_registered(button)
            if valid and tidal_helpers.get_irq_handler(button.pin) is None:
                self._register_irq(button)

            if valid and button.should_autorepeat() and self._autorepeating_button == None:
                self._autorepeating_button = button
                self._autorepeat_timer = get_scheduler().after(self.autorepeat_delay_time, self._autorepeat_delay_expired)

        if self._autorepeating_button and self._autorepeating_button.state == 1:
            # Button no longer down
            self._cancel_autorepeat()

        if button_changed_state:
            get_scheduler().reset_inactivity()

    def _send_callback_for_button(self, pin_number, *args):
        # if pin_number is eg JOY_LEFT, and the current rotation is 180, this
        # function will actually call the callback set for JOY_RIGHT, if there
        # is one.
        if rotated_pin := _rotations[self._rotation].get(pin_number, None):
            pin_number = rotated_pin
        button = self._callbacks.get(pin_number, None)
        if button and button.callback:
            button.callback(*args)

    def _autorepeat_delay_expired(self):
        ab = self._autorepeating_button
        if ab:
            # print(f"Starting autorepeat of {ab.pin}")
            self._autorepeat_timer = get_scheduler().periodic(ab.autorepeat, self._send_autorepeat)

    def _send_autorepeat(self):
        # print(f"Autorepeating {self._autorepeating_button.pin} whose state is {self._autorepeating_button.pin.value()}")
        get_scheduler().reset_inactivity()
        self._send_callback_for_button(self._autorepeating_button.pin_number)

    def _cancel_autorepeat(self):
        if self._autorepeat_timer:
            # print(f"Cancelling autorepeat of {self._autorepeating_button.pin}")
            self._autorepeat_timer.cancel()
            self._autorepeat_timer = None
        self._autorepeating_button = None

    def deactivate(self):
        global _current
        if not self.is_active():
            return

        # print(f"Deactivating {self}")
        self._cancel_autorepeat()

        for button in self._callbacks.values():
            # print(f"Unregistering {button.pin}")
            tidal_helpers.set_lightsleep_irq(button.pin, None, None)
            if button.updown and button.state == 0:
                # Simulate a button up
                button.state = 1
                self._send_callback_for_button(button.pin_number, False)

        _current = None

    def activate(self):
        global _current
        if self.is_active():
            return

        if _current:
            _current.deactivate()
        _current = self

        # print(f"Activating {self}")
        for button in self._callbacks.values():
            self._register_irq(button)

    def clear_callbacks(self):
        for button in self._callbacks.values():
            self.on_press(button.pin, None)

    def get_rotation(self):
        return self._rotation

    def set_rotation(self, rotation):
        # TODO handle sending on_up_down(False) calls to any button that was held down when this rotate call occurs
        self._rotation = rotation


# badge.team compat APIs

BTN_A = tidal.BUTTON_A
BTN_B = tidal.BUTTON_B
BTN_UP = tidal.JOY_UP
BTN_DOWN = tidal.JOY_DOWN
BTN_LEFT = tidal.JOY_LEFT
BTN_RIGHT = tidal.JOY_RIGHT
BTN_UP = tidal.JOY_UP
BTN_SELECT = tidal.JOY_CENTRE
BTN_START = tidal.BUTTON_FRONT

def get_current_buttons():
    global _current
    if _current is None:
        _current = Buttons()
        _current.activate()
    return _current

def value(button):
    # All our buttons are active low and it seems the API expects truthy value to mean "pressed"
    return not button.value()

def attach(button, callback):
    b = get_current_buttons()
    b.on_up_down(callback)

def detach(button, callback):
    b = get_current_buttons()
    b.on_up_down(None)

def getCallback(button):
    if _current is None:
        return None
    else:
        return _current.get_callback(button)

def rotate(value):
    get_current_buttons().set_rotation(value)
