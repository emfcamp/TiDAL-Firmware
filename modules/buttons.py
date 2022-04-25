import tidal
from machine import Timer

# Only one Buttons object can be active at a time - whichever most recently
# called activate() gets the interrupts.
_current = None

class Button:
    def __init__(self, pin, callback, updown, autorepeat):
        self.pin = pin
        self.callback = callback
        self.updown = updown
        self.autorepeat = autorepeat
        self.state = pin.value()

    def check_state(self):
        new_state = self.pin.value()
        if new_state != self.state:
            self.state = new_state
            if self.updown:
                self.callback(self.pin, self.state == 0)
            elif self.state == 0:
                # Button pressed down
                self.callback(self.pin)

    def should_autorepeat(self):
        return (not self.updown) and self.autorepeat and (self.state == 0)


class Buttons:

    autorepeat_delay_time = 200 # ms
    autorepeat_time = 200 # ms

    def __init__(self):
        self._callbacks = {} # str(pin) -> Button
        self._timer = Timer(tidal.TIMER_ID_BUTTONS)
        self._autorepeating_button = None

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
                button.pin.irq(None)

    def _is_registered(self, button):
        return str(button.pin) in self._callbacks

    def _register_irq(self, button):
        button.state = button.pin.value()
        button.pin.irq(lambda _: self._irq_triggered(button))

    def _irq_triggered(self, button):
        # You can't actually trust button.pin.value() in an edge-triggered IRQ.
        # The voltage at which it triggers is not necessarily the same as the
        # 0-1 threshold, plus it depends how quickly this code gets to run
        # versus how quickly the voltage changes. Use a short timer to handle
        # this and provide a bit of debouncing as well

        # Any further button event cancels any autorepeat
        self._autorepeating_button = None

        self._timer.init(mode=Timer.ONE_SHOT, period=10, callback=lambda t: self._timer_fired())

    def _timer_fired(self):
        ab = self._autorepeating_button
        if ab:
            ab.check_state()
            if ab.state == 0:
                # Still down
                ab.callback(ab.pin)
            if not self._is_registered(ab) or ab.state == 1:
                # Stop repeating
                self._timer.deinit()
                self._autorepeating_button = None
        else:
            for button in self._callbacks.values():
                button.check_state()
                if self._is_registered(button) and button.should_autorepeat() and self._autorepeating_button == None:
                    self._autorepeating_button = button
                    self._timer.init(mode=Timer.ONE_SHOT, period=self.autorepeat_delay_time, callback=lambda t: self._autorepeat_delay_expired())

    def _autorepeat_delay_expired(self):
        if self._autorepeating_button:
            self._timer.init(mode=Timer.PERIODIC, period=self._autorepeating_button.autorepeat, callback=lambda t: self._timer_fired())

    def deactivate(self):
        global _current
        if not self.is_active():
            return

        self._timer.deinit()

        for button in self._callbacks.values():
            # This doesn't actually completely disable the IRQ, but close enough from Python's pov
            button.pin.irq(None)

        _current = None

    def activate(self):
        global _current
        if _current:
            _current.deactivate()
        _current = self

        for button in self._callbacks.values():
            self._register_irq(button)

    def clear_callbacks(self):
        for button in self._callbacks.values():
            self.on_press(button.pin, None)
