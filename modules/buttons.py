import time

class Buttons:
    def __init__(self):
        # stack of arrays of callbacks (so you can push/pop entire collections of callbacks)
        self._press_callbacks = [[]]

    def on_press(self, pin, callback):
        current = self._press_callbacks[-1]
        for (i, (existing_pin, _)) in enumerate(current):
            if existing_pin == pin:
                del current[i]
                break
        current.append((pin, callback))

    def push(self):
        self._press_callbacks.append([])

    def pop(self):
        del _self.press_callbacks[-1]
        if len(self._press_callbacks) == 0:
            self.push()

    def clear_callbacks(self):
        self._press_callbacks[-1] = []

    # TODO burn this once the IRQ stuff is sorted out
    def poll(self):
        for (pin, callback) in self._press_callbacks[-1]:
            if pin.value() == 0:
                callback(pin)
