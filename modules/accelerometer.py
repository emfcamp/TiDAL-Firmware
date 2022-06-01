from tidal import i2c
import time
import ustruct

_inited = False
_active = False

# See https://github.com/emfcamp/TiDAL-Hardware/blob/main/datasheets/2004281102_QST-QMA7981_C457290.pdf

DEVICE_ADDR = 18

REG_DXL = 0x1
REG_STEP_CNT_0 = 0x07
REG_STEP_CNT_1 = 0x08
REG_STEP_CNT_2 = 0x0E
REG_FSR = 0x0F
REG_BW = 0x10
REG_PM = 0x11
REG_STEP_CONF_0 = 0x12
REG_STEP_CONF_1 = 0x13
REG_STEP_CONF_2 = 0x14
REG_STEP_CONF_3 = 0x15
REG_STEP_CONF_4 = 0x1F # Not actually named in the datasheet...
REG_RESET = 0x36

MCLK_50KHZ = 4
MCLK_500KHZ = 0
DIV_1935 = 2
FSR_4G = 2

# As per the FSR configuration
_scale = 4

def write(reg, val):
    i2c.writeto_mem(DEVICE_ADDR, reg, bytes((val,)))

def init():
    global _inited
    write(REG_RESET, 0xB6)
    time.sleep(0.2)
    write(REG_RESET, 0)
    time.sleep(0.01)

    write(REG_PM, 0xC0 | MCLK_50KHZ)
    write(REG_FSR, 0xF0 | FSR_4G)
    write(REG_BW, 0xE0 | DIV_1935)

    # None of these actually seem to work...
    # write(REG_STEP_CONF_0, 0x82) # STEP_SAMPLE_CNT=?
    # write(REG_STEP_CONF_1, 0x80) # STEP_PRECISION=?
    # write(REG_STEP_CONF_2, 1) # STEP_TIME_LOW=?
    # write(REG_STEP_CONF_3, 0xFF) # STEP_TIME_UP=?
    # write(REG_STEP_CONF_4, 0) # STEP_START_CNT, STEP_COUNT_PEAK, STEP_COUNT_P2P

    _inited = True

def sleep():
    global _active
    if _inited and _active:
        print("Accelerometer sleep")
        write(REG_PM, MCLK_50KHZ)
        _active = False

def check_active():
    global _active
    if not _inited:
        init()
    if not _active:
        write(REG_PM, 0xC0 | MCLK_50KHZ)
        _active = True

def get_step_count():
    check_active()
    data = i2c.readfrom_mem(DEVICE_ADDR, REG_STEP_CNT_0, 2)
    data2 = i2c.readfrom_mem(DEVICE_ADDR, REG_STEP_CNT_2, 1)
    return data[0] + (data[1] << 8) + (data2[0] << 16)

def _read_val(bytes):
    if ((bytes[0] & 1) == 0):
        return 0
    raw = ustruct.unpack("<h", bytes)[0]
    raw = raw >> 2
    return (raw * _scale)/ (1 << 13);

def get_xyz():
    check_active()

    rawdata = i2c.readfrom_mem(DEVICE_ADDR, REG_DXL, 6)
    x = _read_val(rawdata[0:2])
    y = _read_val(rawdata[2:4])
    z = _read_val(rawdata[4:6])
    return (x, y, z)
