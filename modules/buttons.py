import time

# stack of arrays of callbacks (so you can push/pop entire collections of callbacks)
_press_callbacks = [[]]

def on_press(pin, callback):
    current = _press_callbacks[-1]
    for (i, (existing_pin, _)) in enumerate(current):
        if existing_pin == pin:
            del current[i]
            break
    current.append((pin, callback))

def push():
    _press_callbacks.append([])

def pop():
    del _press_callbacks[-1]
    if len(_press_callbacks) == 0:
        push()

def clear_callbacks():
    _press_callbacks[-1] = []

# TODO burn this once the IRQ stuff is sorted out
def poll():
    while True:
        for (pin, callback) in _press_callbacks[-1]:
            if pin.value() == 0:
                callback(pin)

        time.sleep(0.2)
