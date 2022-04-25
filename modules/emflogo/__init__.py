from tidal import display
from app import App
from machine import Timer
import emf_png


class EMFLogo(App):
    app_id = "emflogo"

    def on_start(self):
        super().on_start()
        self.timer = Timer(0)

    def on_wake(self):
        super().on_wake()
        display.vscrdef(40, 240, 40)
        display.vscsad(40)
        display.bitmap(emf_png, 0, 0)
        self.i = 0
        self.timer.init(mode=Timer.PERIODIC, period=10, callback=lambda _: self.update())

    def update(self):
        self.i = (self.i + 1) % 240
        display.vscsad(40 + self.i)
