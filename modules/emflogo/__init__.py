from tidal import display
from app import App
import lodepng
import emf_png

class EMFLogo(App):

    def on_start(self):
        super().on_start()

    def on_activate(self):
        super().on_activate()
        display.vscrdef(40, 240, 40)
        display.vscsad(40)
        (w, h, buf) = lodepng.decode565(emf_png.DATA)
        display.blit_buffer(buf, 0, 0, w, h)
        self.i = 0
        self.timer_task = self.periodic(10, self.update)

    def update(self):
        diff = 1 if self.get_rotation() == 0 else -1
        self.i = (self.i + diff) % 240
        display.vscsad(40 + self.i)

    def on_deactivate(self):
        super().on_deactivate()
        display.vscsad(40) # Scroll screen back up to top
        self.timer_task.cancel()
