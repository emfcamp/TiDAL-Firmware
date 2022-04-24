import tidal
from buttons import Buttons
from scheduler import get_scheduler
import textwindow

class App:
    app_id = __name__

    # Defaults for TextApp and MenuApp
    BG = tidal.BLUE
    FG = tidal.WHITE

    def __init__(self):
        self.started = False
        self.buttons = Buttons()

    def run_sync(self):
        get_scheduler().main(self)

    def on_start(self):
        if self.buttons:
            self.buttons.on_press(tidal.BUTTON_FRONT, lambda _: self.navigate_back())

    def on_stop(self):
        return NotImplemented

    def on_activate(self):
        return NotImplemented

    def on_deactivate(self):
        return NotImplemented

    def check_for_interrupts(self):
        if self.buttons:
            return self.buttons.check_for_interrupts()
        return False

    def navigate_back(self):
        get_scheduler().switch_app(None)

    def after(self, ms, callback):
        return get_scheduler().after(ms, callback)

    def periodic(self, ms, callback):
        return get_scheduler().periodic(ms, callback)

class TextApp(App):
    def __init__(self):
        super().__init__()
        self.window = textwindow.TextWindow(self.BG, self.FG, self.title)


class MenuApp(App):
    def __init__(self):
        super().__init__()
        self.window = textwindow.Menu(self.BG, self.FG, self.FOCUS_BG, self.FOCUS_FG, self.title, self.choices)

    def on_start(self):
        super().on_start()
        win = self.window
        self.buttons.on_press(tidal.JOY_DOWN, lambda _: win.set_focus_idx(win.focus_idx() + 1))
        self.buttons.on_press(tidal.JOY_UP, lambda _: win.set_focus_idx(win.focus_idx() - 1))
        def select(_):
            self.choices[win.focus_idx()][1]()
        self.buttons.on_press(tidal.JOY_CENTRE, select, autorepeat=False)
        self.buttons.on_press(tidal.BUTTON_A, select, autorepeat=False)
        self.buttons.on_press(tidal.BUTTON_B, select, autorepeat=False)

    def on_activate(self):
        super().on_activate()
        self.window.cls()
