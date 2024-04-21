from app import MenuApp, Menu
from buttons import Buttons
from textwindow import TextWindow, DialogWindow
from scheduler import get_scheduler 
import time
import settings
import tidal
import orientation
import _thread
import vga2_bold_16x32
import tidal_authentication
import binascii
import machine
import ecc108a
import hashlib


class PromptPermission(DialogWindow):

    def __init__(self, slot_id=None, *args, **kwargs):
        self.slot_id = slot_id
        return super(*args, **kwargs)

    def redraw(self):
        self.cls()
        self.println("Press the joystick to approve")
    


class Authenticator(MenuApp):
    APP_ID = "authenticator"
    TITLE = "Authenticator"

    @property
    def CHOICES(self):
        # The crypto chip has 16 slots
        choices = [self.make_slot_select(slot_id) for slot_id in range(16)]
        print(choices)
        return choices

    def make_slot_select(self, slot_id):
        name = settings.get(f"auth_slot_{slot_id}_name", None)
        if name and len(name) > 5:
            name = name[:5]
        if not name:
            name = f"Unused slot {slot_id}"
        registered_date = settings.get(f"auth_slot_{slot_id}_registered", "")
        return (name + " " + registered_date, print)

    def reallocate_slot(self, slot_id):
        settings.delete(f"auth_slot_{slot_id}_name")
        settings.delete(f"auth_slot_{slot_id}_registered")
        settings.save()

def cycle_leds():
    tidal.led_power_on()
    tidal.led[0] = (tidal.led[0][2], ) + tidal.led[0][0:2]
    tidal.led.write()


def trigger_wink(slot_id=None):
    from app_launcher import Launcher
    launcher = Launcher._singleton
    authenticator_app = launcher._apps.get('authenticator.Authenticator')
    if authenticator_app is None:
        authenticator_app = launcher._apps['authenticator.Authenticator'] = Authenticator()
    schedule = get_scheduler()
    schedule.switch_app(authenticator_app)
    tidal.led_power_on(True)
    tidal.led[0] = (255, 255, 0)
    flasher = authenticator_app.periodic(250, cycle_leds)
    okay = authenticator_app.yes_no_prompt("Sign %d?" % slot_id, font=vga2_bold_16x32)
    tidal.led[0] = (0, 0, 0)
    tidal.led.write()
    tidal.led_power_on(False)
    flasher.cancel()
    return okay

prompting = False
def allow_interrupt_when_authenticating():
    def check_for_wink():
        global prompting
        requested, slot_id, application_param = tidal_authentication.get_authentication_requested()
        operation = tidal_authentication.get_authentication_operation()
        if requested == False:
            return
        elif prompting:
            # An earlier periodic invocation is asking
            return
        else:
            prompting = True
            name = binascii.hexlify(application_param).decode('latin-1')
            
            if operation == 1: # Registration request
                # Re-use an old slot for this application, if possible
                if slot_id is None:
                    for i in range(16):
                        if settings.get(f"auth_slot_{i}_name", "") == name:
                            slot_id = i
                            break
                
                # If not, find an unused slot
                if slot_id is None:
                    for i in range(16):
                        if not settings.get(f"auth_slot_{i}_name", ""):
                            slot_id = i
                            break
                
                # No slots available, cancel the approval
                if slot_id is None:
                    tidal_authentication.set_authentication_approval(False)
                    prompting = False
                    return
                else:
                    tidal_authentication.set_authentication_slot(slot_id)
            elif operation == 3: # Authenticate request
                if slot_id:
                    # Check the application parameter matches
                    expected_name = settings.get(f"auth_slot_{slot_id}_name", "")
                    if name != expected_name:
                        tidal_authentication.set_authentication_mismatch()
                        prompting = False
                        return
            
            # Prompt the user for permission
            response = trigger_wink(slot_id)
            if response:
                # If approved, save the metadata
                settings.set(f"auth_slot_{slot_id}_name", f"{name}")
                settings.set(f"auth_slot_{slot_id}_registered", "%04d-%02d-%02d" % (machine.RTC().datetime()[:3]))
                settings.save()

                try:
                    to_sign = tidal_authentication.get_to_sign()
                    if tidal_authentication.get_authentication_operation() == 1:
                        # This is a register request, overwrite the handle at byte 66
                        to_sign = bytearray(to_sign)
                        to_sign[66] = slot_id
                        to_sign = bytes(to_sign)
                        # This is registration, so generate a key
                        ecc108a.genkey(slot_id)
                    print("material", to_sign)
                    print("slot", slot_id)
                    pubkey = ecc108a.get_pubkey(slot_id)
                    tidal_authentication.set_pubkey(pubkey)
                    print("pubkey", pubkey)
                    signature = ecc108a.full_sign(slot_id, to_sign)
                    print("sig", signature)
                    tidal_authentication.set_signature(signature)
                    tidal_authentication.set_authentication_approval(response)
                except OSError:
                    # Retry
                    pass
            prompting = False
    scheduler = get_scheduler()
    scheduler.periodic(2500, check_for_wink)