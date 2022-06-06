from tidal import i2c
import ustruct
import time

_inited = False

# See https://github.com/emfcamp/TiDAL-Hardware/blob/main/datasheets/QMC7983%20Datasheet%20-NCP-Rev1.0.pdf

DEVICE_ADDR = 0x2C


REG_XYZ = 0x0
REG_STATUS = 0x6
REG_TOUT_0 = 0x7
REG_TOUT_1 = 0x8
REG_CFG = 0x9
REG_RST = 0xA
REG_FBR = 0xB
REG_OTP_RDY = 0xC
REG_CHIPID = 0xD

_scale = 8

def write(reg, val):
    i2c.writeto_mem(DEVICE_ADDR, reg, bytes((val,)))

def read(reg, count):
    return i2c.readfrom_mem(DEVICE_ADDR, reg, count)

def read_val(bytes):
    return (ustruct.unpack("<h", bytes)[0] / 32768) * _scale

def init():
    global _inited
    write(REG_RST, 0x80)
    time.sleep(0.1)

    write(REG_FBR, 0x0F)

    if (_scale == 16):
        write(REG_CFG, 0x3D)
    if (_scale == 12):
        write(REG_CFG, 0x2D)
    if (_scale == 8):
        write(REG_CFG, 0x1D)
    if (_scale == 2):
        write(REG_CFG, 0x0D)

    _inited = True

def sleep():
    global _inited
    if _inited:
        print("Magnetometer sleep")
        write(REG_CFG, 0x00)
        _inited = False

def check_ready():
    ready = read(REG_STATUS, 1)[0] & 1
    if not _inited or not ready:
        init()

def get_xyz():
    try:
        check_ready()
        rawdata = read(REG_XYZ, 6)
    except OSError:
        return (0, 0, 0) # is there something more sensible?

    x = read_val(rawdata[0:2])
    y = read_val(rawdata[2:4])
    z = read_val(rawdata[4:6])
    return (x, y, z)
