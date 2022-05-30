import battery
import tidal
import time
import textwindow
import wifi
import accelerometer
from machine import ADC

# Note, this intentionally doesn't inherit App or TextApp to limit dependencies
# because it is on the critical path from the Recovery Menu.
# But it acts sufficiently like it does, to satisfy the app launcher
class PowerOnSelfTest:
    
    title = "POST"
    
    BG = tidal.BLUE
    FG = tidal.WHITE


    def run_sync(self):
        self.on_start()
        while True:
            self.on_activate()
            time.sleep_ms(100)

    def get_app_id(self):
        return "post"

    def on_start(self):
        self.window = textwindow.TextWindow(self.BG, self.FG, self.title)
        self.timer = 10
        self.window.cls()
        self.i2c_addresses = []#tidal.i2cs.scan()
        self.connecting = False
        self.adc = ADC(tidal.BUTTON_A)
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)

    def update_screen(self):
        win = self.window
        reading = self.read_battery_state()
        if reading[2] < 0.8:
            nan = float('nan')
            win.println("     Raw: {:0.3g}".format(nan))
            win.println(" Voltage: {:0.3g}".format(nan))
            win.println("       %: {:0.1f}".format(nan))
            win.println("Charging: {}".format(None))
        else:
            win.println("     Raw: {:0.3g}".format(reading[2]))
            win.println(" Voltage: {:0.3g}".format(reading[0]))
            win.println("       %: {:0.1f}".format(reading[1]))
            win.println("Charging: {}".format("Yes" if tidal.CHARGE_DET.value() == 0 else "No"))

    def read_battery_state(self):
        """ Returns a tuple of (voltage, percentage, raw adc value) """
        reading = self.adc.read_uv() / 1.0e6
        index = 0
        for i in range(len(battery.BATTERY_CAL)):
            if reading < battery.BATTERY_CAL[i][1]:
                index = i
                break
        lower_bound = (0, 0, 0)
        if index > 0:
            lower_bound = battery.BATTERY_CAL[index-1]

        offset = reading - lower_bound[1]
        slope_v = (battery.BATTERY_CAL[index][0] - lower_bound[0]) / (battery.BATTERY_CAL[index][1] - lower_bound[1])
        voltage = lower_bound[0] + slope_v * offset

        slope_p = (battery.BATTERY_CAL[index][2] - lower_bound[2]) / (battery.BATTERY_CAL[index][1] - lower_bound[1])
        percentage = lower_bound[2] + slope_p * offset
        return (voltage, percentage, reading)

    def on_activate(self):
        window = self.window
        #window.cls()
        window.set_next_line(0)
        
        self.update_screen()

        window.println(f"I2C: {self.i2c_addresses}")
        #tidal.enable_peripheral_I2C()
        #p_i2c_addresses = tidal.i2cp.scan() if tidal.i2cp else None
        #window.println(f"I2Cp: {p_i2c_addresses}")
        
        tidal.led_power_on()
        tidal.led[0] = (255, 128, 0)
        tidal.led.write()
        
        buttons = [btn.value() for btn in tidal.ALL_BUTTONS]
        buttons = "".join(map(str, buttons))
        window.println(f"BTN: {buttons}")
        
        if self.timer:
            if tidal.BUTTON_B.value() == 0:
                self.timer -= 1
            else:
                self.timer = min(self.timer + 1, 10)
            window.println(f"Wifi: Hold B {self.timer:2}")
        else:
            if not self.connecting:
                wifi.connect()
                self.connecting = True
            window.println(f"Wifi: {wifi.get_sta_status()}")
            window.println(f"IP: {wifi.get_ip()}")
        try:
            pos = accelerometer.get_xyz()
        except OSError:
            pos = None
        window.println(f"Accel: {pos}")
