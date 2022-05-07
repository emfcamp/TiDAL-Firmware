import network
import settings
import time

DEFAULT_RETRY = 5

interface = None
_ssid = None
_password = None
_ap = None

def get_ssid():
    if _ssid:
        return _ssid
    else:
        return settings.get("wifi_ssid", "badge")

def get_password():
    if _password:
        return _password
    else:
        return settings.get("wifi_password", "badge")

def get_ip():
    if isuporconnected():
        return interface.ifconfig()[0]
    else:
        return None

def is_configured_sta():
    return get_ssid() and not settings.get("wifi_ap")

def is_ap():
    if interface:
        return not is_sta()
    else:
        return get_ssid() and settings.get("wifi_ap")

def is_sta():
    # WLAN constructor always returns shared objects so this works
    return interface == network.WLAN(network.STA_IF)

def isuporconnected():
    """Returns true if wifi is configured in AP mode, or if connected to a Wi-Fi base station"""
    if is_sta():
        return isconnected()
    else:
        return interface and interface.active()

def isconnected():
    return interface is not None and interface.isconnected()

def configure_interface():
    global interface, _ap
    if _ap is None:
        _ap = settings.get("wifi_ap")
    new_interface = network.WLAN(network.AP_IF if _ap else network.STA_IF)
    if interface and new_interface != interface:
        interface.active(False)
    interface = new_interface
    interface.active(True)
    if _ap:
        interface.config(essid=get_ssid(), password=get_password())
    else:
        # Unless you set this, connection attempts with bad password never fail
        interface.config(reconnects=settings.get("wifi_reconnects", DEFAULT_RETRY))

def status():
    if interface:
        return interface.status()
    else:
        return network.STAT_IDLE

def connect(ssid=None, password=None):
    global interface, _ssid, _password, _ap
    if is_ap() and not ssid:
        # Asking to connect but not providing non-AP creds
        print("Cannot call connect() with no SSID when stored creds are for AP mode")
        return False

    _ap = False
    if ssid:
        _ssid = ssid
        _password = password

    configure_interface()

    interface.connect(get_ssid(), get_password())
    # Note, you're not actually connected at this point. Caller has to wait
    # until status() returns network.STAT_GOT_IP
    return True

def save_settings():
    settings.set("wifi_ap", _ap)
    settings.set("wifi_ssid", _ssid)
    settings.set("wifi_password", _password)
    settings.save()
