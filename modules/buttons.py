import tidal
import tidal_helpers
from machine import Timer
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


class Buttons:

    autorepeat_delay_time = 200 # ms
    autorepeat_time = 200 # ms

    def __init__(self):
        self._callbacks = {} # str(pin) -> Button
        self._timer = Timer(tidal.TIMER_ID_BUTTONS)
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
        button.state = button.pin.value()
        level = 1 if button.state == 0 else 0
        # print(f"Registering {button.pin} for {level}")
        tidal_helpers.set_lightsleep_irq(button.pin, level, _button_irq)

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
            if new_state != button.state:
                # print(f"{button.pin} state changed to {new_state}")
                button.state = new_state
                if button.updown:
                    button.callback(button.pin, button.state == 0)
                elif button.state == 0:
                    # Button pressed down
                    button.callback(button.pin)

                # Check that, if we made a callback, that it didn't unregister the button
                if self._is_registered(button):
                    # and if it didn't, re-enable the interrupt
                    self._register_irq(button)

            # if button.check_state() and self._is_registered(button):
            # if self._is_registered(button) and button.should_autorepeat() and self._autorepeating_button == None:
            #     self._autorepeating_button = button
            #     self._timer.init(mode=Timer.ONE_SHOT, period=self.autorepeat_delay_time, callback=lambda t: self._autorepeat_delay_expired())



    # def _irq_triggered(self, button):
    #     # You can't actually trust button.pin.value() in an edge-triggered IRQ.
    #     # The voltage at which it triggers is not necessarily the same as the
    #     # 0-1 threshold, plus it depends how quickly this code gets to run
    #     # versus how quickly the voltage changes. Use a short timer to handle
    #     # this and provide a bit of debouncing as well

    #     # Any further button event cancels any autorepeat
    #     self._autorepeating_button = None

    #     self._timer.init(mode=Timer.ONE_SHOT, period=10, callback=lambda t: self._timer_fired())

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

        print(f"Deactivating {self}")
        self._timer.deinit()
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
        if _current:
            _current.deactivate()
        _current = self

        print(f"Activating {self}")
        for button in self._callbacks.values():
            self._register_irq(button)

    def clear_callbacks(self):
        for button in self._callbacks.values():
            self.on_press(button.pin, None)
