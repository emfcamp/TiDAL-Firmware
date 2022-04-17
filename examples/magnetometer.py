## QMA7983 demonstration code

from machine import I2C
from machine import Pin
import time
import ustruct

# Initialise i2c bus connection
i2c = I2C(scl=Pin(41), sda=Pin(42))

i2c.writeto_mem(44, 0xb, b'\x0f')

# initialise depending on scale
scale = 8
if (scale == 16):
    i2c.writeto_mem(44, 0x9, b'\x3d')
if (scale == 12):
    i2c.writeto_mem(44, 0x9, b'\x2d')
if (scale == 8):
    i2c.writeto_mem(44, 0x9, b'\x1d')
if (scale == 2):
    i2c.writeto_mem(44, 0x9, b'\x0d')

# for some reason from_bytes is ignoring sign
def read_val(bytes):
    return (ustruct.unpack("<h", bytes)[0] / 32768) * scale

while True:
    # read register 6 bit 0 to check for ready

    byte = i2c.readfrom_mem(44, 6, 1);
    if ((byte[0] & 2) != 0):
        print("overflow occured", byte[0])
    
    if ((byte[0] & 1) != 0):
        rawdata = i2c.readfrom_mem(44, 0, 6)
        rawtemp = i2c.readfrom_mem(44, 7, 2)

        x = read_val(rawdata[0:2])
        y = read_val(rawdata[2:4])
        z = read_val(rawdata[4:6])
        t = int.from_bytes(rawtemp, 'little', True)

        print("X {} Y {} Z {} Temperature {}".format(x, y, z, t))

    time.sleep_ms(200)
    
