from tidal import display, BUTTON_A, BUTTON_B
from app import App, task_coordinator
import emf_png


class EMFLogo(App):
    app_id = "emflogo"
    post_wake_interval = interval = 0.01

    def on_wake(self):
        display.vscrdef(40, 240, 40)
        display.vscsad(40)
        display.bitmap(emf_png, 0, 0)
        self.i = 0

    def update(self):
        self.i += 1
        if self.i >= 240:
            self.i = 0
        display.vscsad(40 + self.i)

        if BUTTON_A.value() == 0 and BUTTON_B.value() == 0:
            display.vscsad(40)
            task_coordinator.context_changed("menu")
