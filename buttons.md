# Button examples

Initialise some pin objects to use:

```
>>> from machine import Pin
>>> up = Pin(15, Pin.IN, Pin.PULL_UP)
>>> down = Pin(16, Pin.IN, Pin.PULL_UP)
>>> left = Pin(8, Pin.IN, Pin.PULL_UP)
>>> right = Pin(7, Pin.IN, Pin.PULL_UP)
>>> centre = Pin(9, Pin.IN, Pin.PULL_UP)
>>> btn3 = Pin(6, Pin.IN, Pin.PULL_UP)
>>> btn2 = Pin(2, Pin.IN)
>>> btn1 = Pin(1, Pin.IN, Pin.PULL_UP)
```

simple print the button status in a loop:
```
>>> import time
>>> while True:
>>>    print("U", up.value(), "D", down.value(), "L", left.value(), "R", right.value(), "C", centre.value(), "B3", btn3.value());
>>>    time.sleep_ms(250)
'''

print just the buttons
```
>>> import time
>>> while True:
>>>    print("BTNS {} {} {}".format(btn1.value(), btn2.value(), btn3.value()));
>>>    time.sleep_ms(250)
```

The buttons are all active low, so will read '0' when they are pressed.
BTN2 does not need a pull up set as this is already on the board and any pull up may interfere with the power supply circuit.

# References

- https://docs.micropython.org/en/latest/esp32/quickref.html

