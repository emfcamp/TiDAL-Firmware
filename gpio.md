# General GPIO testing

Note, all these assume the Pin module has already been imported with
```
>>> from machine import Pin
```

## General GPIO

These lines go to the top board and to the edge conenctor on the bottom:

Set all the G{x} pins to input.
```
>>> g0 = Pin(18, Pin.IN)
>>> g1 = Pin(17, Pin.IN)
>>> g2 = Pin(4, Pin.IN)
>>> g3 = Pin(5, Pin.IN)
```

## LED power enable

The LED power enable is an active low signal, so set 0 to power the LED up.

```
>>> led_pwren = Pin(3, Pin.OUT)
```

To turn power on
```
>>> led_pwren.off()
```

To turn power off

```
>>> led_pwren.on()
```

## LCD control signals

The LCD power enable and backlight enable signals are both active low gpios.
The backlight can be enabled without powering the LCD module on.

```
>>> lcd_pwr =  Pin(39, Pin.OUT)
>>> lcd_blen = Pin(0, Pin.OUT)
```

to power on the backlight:
```
>>> lcd_blen.off()
```

to power off the backlight:
```
>>> lcd_blen.on();
```

## Charge detect

the charge detect line comes from the battery charger and is 0 for charging and 1 for not.

```
>>> charge_det = Pin(26, Pin.IN, Pin.PULL_UP)
>>> charge_det.value()
```

## Auth wakeup

```
>>> auth_wake = Pin(21, Pin.OUT)
>>> auth_wake.on()
>>> auth_wake.off))
```


