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
```

simple print the button status in a loop:
```
>>> import time
>>> while True:
>>>    print("U", up.value(), "D", down.value(), "L", left.value(), "R", right.value(), "C", centre.value(), "B3", btn3.value());
time.sleep_ms(250)
'''

# References

- https://docs.micropython.org/en/latest/esp32/quickref.html
