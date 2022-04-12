## QMA7981 accelerometer example code

from machine import I2C
from machine import Pin
import time
import ustruct

i2c = I2C(scl=Pin(41), sda=Pin(42))

# reset
i2c.writeto_mem(18, 0x36, b'\xb6')
time.sleep(0.2)
i2c.writeto_mem(18, 0x36, b'\x00')

## todo check post reset state

# power up, set to 4G, 1024Hz bandwidth
scale = 4
i2c.writeto_mem(18, 0x11, b'\xc1')
i2c.writeto_mem(18, 0xf,  b'\x01')
i2c.writeto_mem(18, 0x10,  b'\x05')

def read_val(bytes):
    if ((bytes[0] & 1) == 0):
        return 0
    raw = ustruct.unpack("<h", bytes)[0]
    raw = raw >> 2
    return (raw * scale)/ (1 << 13);

while True:
    rawdata = i2c.readfrom_mem(18, 1, 6)
    x = read_val(rawdata[0:2])
    y = read_val(rawdata[2:4])
    z = read_val(rawdata[4:6])


    print("X {} Y {} Z {} RAW {}".format(x,y,z,rawdata))
    time.sleep_ms(200)
