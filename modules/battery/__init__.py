from app import TextApp
from machine import ADC
import tidal

import tidal_helpers

# Battery Voltage, BTN_A V, Battery %
BATTERY_CAL = [
    (3.10, 2.18,   0), # UVLO will be active at 3.10V, so the BTN_A voltage is a guess.
    (3.15, 2.27,   0.2),
    (3.20, 2.36,   0.4),
    (3.25, 2.40,   0.8),
    (3.30, 2.45,   1.0),
    (3.35, 2.49,   1.2),
    (3.40, 2.52,   1.4),
    (3.45, 2.57,   2.0),
    (3.50, 2.61,   3.0),
    (3.55, 2.65,   4.0),
    (3.60, 2.69,   5.0),
    (3.65, 2.72,   8.0),
    (3.70, 2.77,  12.0),
    (3.75, 2.80,  25.0),
    (3.80, 2.86,  40.0),
    (3.85, 2.90,  55.0),
    (3.90, 2.94,  63.0),
    (3.95, 2.98,  70.0),
    (4.00, 3.02,  78.0),
    (4.05, 3.06,  82.0),
    (4.10, 3.10,  90.0),
    (4.15, 3.14,  95.0),
    (4.20, 3.18, 100.0)
]


class Battery(TextApp):

    TITLE = "Battery"

    def __init__(self):
        super().__init__()
        self.pin = tidal.BUTTON_A
        self.update_interval_ms = 10000 # Sample every 100ms
        self.average_discharge = 0
        self.sample_count = 0
        self.max_time_seconds = 3600 # Maximum expected battery life in seconds
        self.time_remaining_seconds = self.max_time_seconds
        self.adc = ADC(self.pin)
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)
        self.timer = None
        self.sample_timer = None
        self.last_reading = self.read_battery_state()
        self.engineer_mode = False
        # Restore the pin pull up so the button works normally again.
        self.pin.init(self.pin.IN, self.pin.PULL_UP)
        self.samples = []
        self.max_samples = 30

    def update_stats(self):
        if tidal.CHARGE_DET.value() == 0:
            return  # Don't update if we're charging.
        reading = self.read_battery_state()
        diff = self.last_reading[1] - reading[1]
        self.sample_count += 1
        self.samples.append(reading[1])
        if len(self.samples) > self.max_samples:
            self.samples.pop(0)
        self.average_discharge += (diff - self.average_discharge) / min(20.0, float(self.sample_count))
        if self.average_discharge <= 0:
            self.average_discharge = 0
            self.time_remaining_seconds = self.max_time_seconds
        else:
            self.time_remaining_seconds = reading[1] / ((self.average_discharge * 1000.0) / self.update_interval_ms)
            if self.time_remaining_seconds > self.max_time_seconds:
                self.time_remaining_seconds = self.max_time_seconds
        self.last_reading = reading

    def display_graph(self):
        totalTime = self.max_samples * self.update_interval_ms / (60*1000.0)
        self.window.println(" {:0.0f} Minutes".format(totalTime), 10)

        display = self.window.display
        fg = tidal.WHITE
        bg = tidal.BLACK
        # x max is width
        # y max is height
        height = int(display.height()/2.0)
        x = 0
        y = height
        xd = int(display.width() / self.max_samples)
        for sample in self.samples:
            pixels = int(sample * height/100.0)
            display.fill_rect(x, height, xd, height - pixels, bg)
            display.fill_rect(x, display.height() - pixels, xd, pixels, fg)
            x += xd
            if x > display.width():
                break
        if x < display.width():
            display.fill_rect(x, y, display.width()-x, height, bg)



    def update_screen(self):
        win = self.window
        win.set_next_line(0)
        win.println()
        reading = self.read_battery_state()
        if reading[2] < 1.5:
            win.println("  Unavailable  ")
            win.clear_from_line()
            return

        if self.engineer_mode:
            win.println("     Raw: {:0.3g}".format(reading[2]), 1)
            win.println(" Voltage: {:0.3g}".format(reading[0]), 2)
            win.println("       %: {:0.2f}".format(reading[1]), 3)
        else:
            win.println("", 1)
            win.println("   %: {:0.0f}".format(reading[1]), 2)
            win.println("", 3)
        if tidal.CHARGE_DET.value() == 0:
            win.println(" Charging: Yes", 4)
            win.println(" ", 5)
            win.println(" ", 6)
        else:
            win.println(" Charging: No", 4)
            if self.sample_timer is not None:
                win.println(" ", 5)
                win.println("Remaining: {:0.0f}m".format(self.time_remaining_seconds/60.0), 6)
            else:
                win.println(" Press Joystick", 5)
                win.println("  to monitor", 6)

        win.progress_bar(8, int(reading[1]))
        if self.sample_timer is not None:
            self.display_graph()


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

    def change_engineering_mode(self):
        self.engineer_mode = not self.engineer_mode
        self.update_screen()

    def change_monitor_mode(self):
        if self.sample_timer is not None:
            self.stop_monitoring()
            self.window.cls()
            self.update_screen()
        else:
            self.start_monitoring()

    def on_start(self):
        super().on_start()
        self.buttons.on_press(tidal.BUTTON_B, self.change_engineering_mode)
        self.buttons.on_press(tidal.JOY_CENTRE, self.change_monitor_mode)

    def start_monitoring(self):
        if self.sample_timer is None:
            self.sample_timer = self.periodic(self.update_interval_ms, self.update_stats)

    def stop_monitoring(self):
        if self.sample_timer is None:
            return
        self.sample_timer.cancel()
        self.sample_timer = None

    def on_activate(self):
        super().on_activate()
        # Make sure the pullup is disabled.
        self.pin.init(self.pin.IN, None)
        self.update_screen()
        if self.timer is None:
            self.timer = self.periodic(1000, self.update_screen)

    def on_deactivate(self):
        super().on_deactivate()
        # Restore the pin pull up so the button works normally again.
        self.pin.init(self.pin.IN, self.pin.PULL_UP)
        if self.timer:
            self.timer.cancel()
            self.timer = None


