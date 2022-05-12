import network, time, machine
import settings
import tidal_helpers

_STA_IF = network.WLAN(network.STA_IF)
_AP_IF  = network.WLAN(network.AP_IF)

_DEFAULT_TIMEOUT  = 20

def get_default_ssid():
    return settings.get("wifi_ssid", "badge")

def get_default_password():
    return settings.get("wifi_password", "badge")

def get_sta_status():
    return _STA_IF.status()

def get_ssid():
    if ssid := _STA_IF.config("essid"):
        return ssid
    else:
        return get_default_ssid()

def get_ip():
    if status():
        return ifconfig()[0]
    else:
        return None

def accesspoint_get_ip():
    if accesspoint_status():
        return accesspoint_ifconfig()[0]
    else:
        return None

def save_defaults(ssid, password):
    settings.set("wifi_ssid", ssid)
    settings.set("wifi_password", password)
    settings.save()

# Rest of file is adapted from https://github.com/badgeteam/ESP32-platform-firmware/blob/master/firmware/python_modules/shared/wifi.py
# See license info https://github.com/badgeteam/ESP32-platform-firmware#license-and-information

# STATION MODE
# ------------

def connect(*args):
    '''
    Connect to a WiFi network
    :param ssid: optional, ssid of network to connect to
    :param password: optional, password of network to connect to
    '''
    _STA_IF.active(True)
    # HACK: set tx power to minimum
    tidal_helpers.esp_wifi_set_max_tx_power(8)
    if len(args) == 0:
        if password := get_default_password():
            _STA_IF.connect(get_default_ssid(), password)
        else:
            _STA_IF.connect(get_default_ssid())
    elif len(args) == 1:
        _STA_IF.connect(args[0])
    elif len(args) == 2:
        _STA_IF.connect(args[0], args[1])
    else:
        raise Exception('Expected either 0 (default network), 1 (ssid) or 2 (ssid, password) parameters.')

def disconnect():
    '''
    Disconnect from the WiFi network
    '''
    _STA_IF.disconnect()

def stop():
    '''
    Disconnect from the WiFi network and disable the station interface
    '''
    _STA_IF.disconnect()
    _STA_IF.active(False)

def status():
    '''
    Connection status of the station interface
    :return: boolean, connected
    '''
    return _STA_IF.isconnected()

def wait(duration=_DEFAULT_TIMEOUT):
    '''
    Wait until connection has been made to a network using the station interface
    :return: boolean, connected
    '''
    t = duration
    while not status():
        if t <= 0:
            break
        t -= 1
        time.sleep(1)
    return status()

def scan():
    '''
    Scan for WiFi networks
    :return: list, wifi networks [SSID, BSSID, CHANNEL, RSSI, AUTHMODE1, AUTHMODE2, HIDDEN]
    '''
    _STA_IF.active(True)
    return _STA_IF.scan()

def ifconfig(newConfig=None):
    '''
    Get or set the interface configuration of the station interface
    :return: tuple, (ip, subnet, gateway, dns)
    '''
    if newConfig:
        return _STA_IF.ifconfig(newConfig)
    else:
        return _STA_IF.ifconfig()

# ACCESS POINT MODE
# -----------------

def accesspoint_start(ssid, password=None):
    '''
    Create a WiFi access point
    :param ssid: SSID of the network
    :param password: Password of the network (optional)
    '''
    if password and len(password) < 8:
        raise Exception("Password too short: must be at least 8 characters long")
    _AP_IF.active(True)
    if password:
        _AP_IF.config(essid=ssid, authmode=network.AUTH_WPA2_PSK, password=password)
    else:
        _AP_IF.config(essid=ssid, authmode=network.AUTH_OPEN)

def accesspoint_status():
    '''
    Accesspoint status
    :return: boolean, active
    '''
    return _AP_IF.active()

def accesspoint_stop():
    '''
    Disable the accesspoint
    '''
    _AP_IF.active(False)

def accesspoint_ifconfig(newConfig=None):
    '''
    Get or set the interface configuration of the accesspoint interface
    :return: tuple, (ip, subnet, gateway, dns)
    '''
    if newConfig:
        return _AP_IF.ifconfig(newConfig)
    else:
        return _AP_IF.ifconfig()

# EXTRAS
# -----------------

# NOTE(tomsci): RTC.ntp_sync() not a thing in our micropython version

# def ntp(onlyIfNeeded=True, server='pool.ntp.org'):
#     '''
#     Synchronize the system clock with NTP
#     :return: boolean, synchronized
#     '''
#     if onlyIfNeeded and time.time() > 1482192000:
#         return True #RTC is already set, sync not needed
#     rtc = machine.RTC()
#     if not status():
#         return False # Not connected to a WiFi network
#     return rtc.ntp_sync(server)
