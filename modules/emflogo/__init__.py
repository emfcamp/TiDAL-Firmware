from tidal import display
from app import App
import emf_png

class EMFLogo(App):

    def on_start(self):
        super().on_start()

    def on_activate(self):
        self.set_rotation(0) # We're portrait only
        super().on_activate()
        display.vscrdef(40, 240, 40)
        display.vscsad(40)
        display.bitmap(emf_png, 0, 0)
        self.i = 0
        self.timer_task = self.periodic(10, self.update)

    def update(self):
        self.i = (self.i + 1) % 240
        display.vscsad(40 + self.i)

    def on_deactivate(self):
        display.vscsad(40) # Scroll screen back up to top
        self.timer_task.cancel()
