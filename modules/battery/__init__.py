from app import TextApp
from machine import ADC
import tidal
import tidal_helpers

# Battery Voltage, BTN_A V, Battery %
BATTERY_CAL = [
    (3.10, 2.18,   0), # UVLO will be active at 3.10V, so the BTN_A voltage is a guess.
    (3.15, 2.27,   0),
    (3.20, 2.36,   0),
    (3.25, 2.40,   1),
    (3.30, 2.45,   1),
    (3.35, 2.49,   1),
    (3.40, 2.52,   1),
    (3.45, 2.57,   2),
    (3.50, 2.61,   3),
    (3.55, 2.65,   4),
    (3.60, 2.69,   5),
    (3.65, 2.72,   8),
    (3.70, 2.77,  12),
    (3.75, 2.80,  25),
    (3.80, 2.86,  40),
    (3.85, 2.90,  55),
    (3.90, 2.94,  63),
    (3.95, 2.98,  70),
    (4.00, 3.02,  78),
    (4.05, 3.06,  82),
    (4.10, 3.10,  90),
    (4.15, 3.14,  95),
    (4.20, 3.18, 100)
]


class Battery(TextApp):

    TITLE = "Battery"

    def __init__(self):
        super().__init__()
        self.pin = tidal.BUTTON_A

    def update_screen(self, full=True):
        win = self.window
        reading = self.read_battery_state()
        win.println("     Raw:{}  ".format(reading[2]), 1)
        win.println(" Voltage:{}  ".format(reading[0]), 2)
        win.println("       %:{}  ".format(reading[1]), 3)
        win.println("Charging:{}  ".format("Yes" if tidal.CHARGE_DET.value() == 1 else "No"), 4)

        self.window.progress_bar(7, int(reading[1]))


    def read_battery_state(self):
        """ Returns a tuple of (voltage, percentage, raw adc value) """
        reading = self.adc.read_uv() / 1.0e6
        index = 0
        for i in range(len(BATTERY_CAL)):
            if reading < BATTERY_CAL[i][1]:
                index = i
                break
        lower_bound = (0, 0, 0)
        if index > 0:
            lower_bound = BATTERY_CAL[index-1]

        offset = reading - lower_bound[1]
        slope_v = (BATTERY_CAL[index][0] - lower_bound[0]) / (BATTERY_CAL[index][1] - lower_bound[1])
        voltage = lower_bound[0] + slope_v * offset

        slope_p = (BATTERY_CAL[index][2] - lower_bound[2]) / (BATTERY_CAL[index][1] - lower_bound[1])
        percentage = lower_bound[2] + slope_p * offset
        return (voltage, percentage, reading)

    def on_start(self):
        super().on_start()
        self.adc = ADC(self.pin)
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)
        self.timer = None

    def on_activate(self):
        super().on_activate()
        # Make sure the pullup is disabled.
        # We should probably disable interrupts from the pin too here.
        self.pin.init(self.pin.IN, None)
        window = self.window
        window.cls()
        self.update_screen()
        if self.timer is None:
            self.timer = self.periodic(500, self.update_screen)

    def on_deactivate(self):
        super().on_deactivate()
        # Restore the pin pull up so the button works normally again.
        self.pin.init(self.pin.IN, self.pin.PULL_UP)
        if self.timer:
            self.timer.cancel()
            self.timer = None


