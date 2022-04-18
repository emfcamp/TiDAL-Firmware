
from machine import Pin
from machine import ADC

adc = ADC(Pin(2, Pin.IN), atten=ADC.ATTN_11DB)

adc.read_uv()
964000

