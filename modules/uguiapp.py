from app import App
from buttons import Buttons
from machine import Signal
from tidal import JOY_UP, JOY_DOWN, JOY_LEFT, JOY_RIGHT, JOY_CENTRE, BUTTON_FRONT

import hardware_setup
# Fix up things the Display constructor in hardware_setup would normally have set
import gui.core.ugui as _ugui_core
_ugui_core.display = hardware_setup.display
_ugui_core.ssd = hardware_setup.ssd

from gui.core.ugui import Screen, ssd

class UguiWindow:
    def __init__(self, screen_cls):
        # We assume Screen.current_screen should be null here.
        # This sequence of calls carefully avoids provoking ugui to creating any asyncio tasks
        Screen.do_gc = False
        self.root_screen = screen_cls()
        Screen.current_screen = None
        self.buttons = Buttons()

    def redraw(self):
        Screen.show(True)
        ssd.show()

class UguiApp(App):
    def __init__(self, screen_cls=None):
        super().__init__()
        window = UguiWindow(screen_cls or self.ROOT_SCREEN)
        self.push_window(window, activate=False)
        self.deactivated_screen = window.root_screen

    def on_start(self):
        super().on_start()
        # Setting BUTTON_FRONT in init is too early due to App.on_start overriding it
        _NEXT = 1
        _PREV = 2
        buttons = self.window.buttons
        buttons.on_press(JOY_RIGHT, lambda: Screen.ctrl_move(_NEXT))
        buttons.on_press(JOY_LEFT, lambda: Screen.ctrl_move(_PREV))
        buttons.on_press(JOY_CENTRE, lambda: Screen.sel_ctrl(), autorepeat=False)
        # ugui uses debounced PushButton objects here instead of the raw pins,
        # but so long as it's something that supports __call__ to get the state
        # it's probably fine (use Signal as it expects true to mean clicked)
        up_sig = Signal(JOY_UP, invert=True)
        down_sig = Signal(JOY_DOWN, invert=True)
        buttons.on_press(JOY_UP, lambda: Screen.adjust(up_sig, 1))
        buttons.on_press(JOY_DOWN, lambda: Screen.adjust(down_sig, -1))
        buttons.on_press(BUTTON_FRONT, self.pop_screen)

    def on_activate(self):
        Screen.current_screen = self.deactivated_screen
        super().on_activate()

    def on_deactivate(self):
        super().on_deactivate()
        self.deactivated_screen = Screen.current_screen
        Screen.current_screen = None

    def on_tick(self):
        # print("tick")
        if len(self.windows) == 1:
            # ie we haven't pushed a textwindow on top of the UguiWindow, or anything
            Screen.show(False)
            ssd.show()

    def pop_screen(self):
        if Screen.current_screen.parent:
            Screen.back()
        else:
            self.navigate_back()
