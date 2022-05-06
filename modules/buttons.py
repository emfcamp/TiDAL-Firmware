import tidal_helpers
from scheduler import get_scheduler
import uasyncio

# Only one Buttons object can be active at a time - whichever most recently
# called activate() gets the interrupts.
_current = None

def _button_irq(pin):
    if _current:
        _current._isr_flag = True

class Button:
    def __init__(self, pin, callback, updown, autorepeat):
        self.pin = pin
        self.callback = callback
        self.updown = updown
        self.autorepeat = autorepeat
        self.state = pin.value()

    def should_autorepeat(self):
        return (not self.updown) and self.autorepeat and (self.state == 0)

    def send_autorepeat(self):
        # print(f"Autorepeating {self.pin} whose state is {self.pin.value()}")
        self.callback(self.pin)

class Buttons:

    autorepeat_delay_time = 200 # ms
    autorepeat_time = 200 # ms

    def __init__(self):
        self._callbacks = {} # str(pin) -> Button
        self._autorepeat_timer = None
        self._autorepeating_button = None
        self._isr_flag = False

    def is_active(self):
        return _current == self

    def on_press(self, pin, callback, autorepeat=True):
        if autorepeat is True:
            autorepeat = self.autorepeat_time
        self._register_button(Button(pin, callback, False, autorepeat))

    def on_up_down(self, pin, callback):
        self._register_button(Button(pin, callback, True, False))

    def _register_button(self, button):
        k = str(button.pin) # Pin really needs to be hashable...
        if button.callback:
            self._callbacks[k] = button
            if self.is_active():
                self._register_irq(button)
        elif self._is_registered(button):
            del self._callbacks[k]
            if self.is_active():
                tidal_helpers.set_lightsleep_irq(button.pin, None, None)

    def _is_registered(self, button):
        return str(button.pin) in self._callbacks

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
        for button in self._callbacks.values():
            new_state = button.pin.value()
            valid = True
            if new_state != button.state:
                # print(f"{button.pin} state changed to {new_state}")
                button.state = new_state
                if button.updown:
                    button.callback(button.pin, button.state == 0)
                elif button.state == 0:
                    # Button pressed down
                    button.callback(button.pin)

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
            # print(f"Cancelling autorepeat of {self._autorepeating_button.pin}")
            self._autorepeat_timer.cancel()
            self._autorepeat_timer = None
            self._autorepeating_button = None

    def _autorepeat_delay_expired(self):
        ab = self._autorepeating_button
        if ab:
            # print(f"Starting autorepeat of {ab.pin}")
            self._autorepeat_timer = get_scheduler().periodic(ab.autorepeat, ab.send_autorepeat)

    def deactivate(self):
        global _current
        if not self.is_active():
            return

        # print(f"Deactivating {self}")
        if self._autorepeat_timer:
            self._autorepeat_timer.cancel()
            self._autorepeat_timer = None
        self._autorepeating_button = None

        for button in self._callbacks.values():
            tidal_helpers.set_lightsleep_irq(button.pin, None, None)
            if button.updown and button.state == 0:
                # Simulate a button up
                button.state = 1
                button.callback(button.pin, False)

        _current = None
        self._isr_flag = False

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
