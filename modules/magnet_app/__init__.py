from app import TextApp
import magnetometer

class Magnetometer(TextApp):
    TITLE = "Magnetometer"
    timer = None

    def on_start(self):
        super().on_start()

    def on_activate(self):
        super().on_activate()
        self.update_screen()
        self.timer = self.periodic(500, self.update_screen)

    def on_deactivate(self):
        self.timer.cancel()
        super().on_deactivate()

    def update_screen(self):
        win = self.window
        win.set_next_line(0)
        win.println()

        (x, y, z) = magnetometer.get_xyz()

        win.println(f"X: {x:0.3g}")
        win.println(f"Y: {y:0.3g}")
        win.println(f"Z: {z:0.3g}")
