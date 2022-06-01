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
    
    BG = tidal.BRAND_ORANGE
    FG = tidal.BLACK


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
        self.i2c_addresses = tidal.i2cs.scan()
        self.connecting = False
        self.error_found = False
        self.buttons_seen = {repr(button):False for button in tidal.ALL_BUTTONS}
        self.adc = ADC(tidal.BUTTON_A)
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)

    def update_screen(self):
        win = self.window
        reading = self.read_battery_state()
        if reading[2] < 0.8:
            self.buttons_seen[repr(tidal.BUTTON_A)] = True
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
        
        i2c = self.i2c_addresses == [18, 44, 96]
        if not i2c and self.window.bg != tidal.ADDITIONAL_RED:
            self.window.bg = tidal.ADDITIONAL_RED
            self.window.fg = tidal.WHITE
            self.window.cls()

        self.update_screen()
        
        window.println("")
        window.println("")

        window.println(f"I2C: {self.i2c_addresses}")
        window.println("")

        tidal.led_power_on()
        tidal.led[0] = (255, 128, 0)
        tidal.led.write()
        
        
        window.println("")
        window.println("")

        buttons = []
        for button in tidal.ALL_BUTTONS:
            val = button.value()
            if val == 0 and button != tidal.BUTTON_A:
                self.buttons_seen[repr(button)] = True
            buttons.append('X' if self.buttons_seen[repr(button)] else '.')
        buttons = "".join(map(str, buttons))
        window.println(f"BTN: {buttons}")
        buttons = all(self.buttons_seen.values())
        
        window.println("")
        window.println("")

        wifi_state = False
        if self.timer:
            self.timer -= 1
            window.println(f"Wifi: Wait for {self.timer:2}")
            window.println("IP: N/A")
        else:
            if not self.connecting:
                wifi.connect()
                self.connecting = True
            window.println(f"Wifi: {wifi.get_sta_status()}")
            window.println(f"IP: {wifi.get_ip()}")
            if wifi.get_sta_status() == 1010:
                wifi_state = True
        try:
            x,y,z = accelerometer.get_xyz()
        except OSError:
            x = y = z = None

        window.println("")
        window.println("")

        window.println("Accel")
        window.println(f"X: {x}")
        window.println(f"Y: {y}")
        window.println(f"Z: {z}")
        
        accel = x != 0 or y != 0 or z != 0
        
        print(f"{buttons}, {accel}, {wifi_state}, {i2c}")
        if buttons and accel and wifi_state and i2c:
            if self.window.bg != tidal.BRAND_NAVY:
                self.window.bg = tidal.BRAND_NAVY
                self.window.fg = tidal.WHITE
                self.window.cls()
