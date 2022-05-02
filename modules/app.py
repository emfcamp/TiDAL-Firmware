import tidal
from buttons import Buttons
from scheduler import get_scheduler
from textwindow import TextWindow, Menu

class App:

    # Defaults for TextApp and MenuApp
    BG = tidal.BLUE
    FG = tidal.WHITE

    def __init__(self):
        self.started = False
        self.windows = []

    def get_app_id(self):
        if name := getattr(self, "app_id", None):
            return name
        else:
            return self.__class__.__name__

    def run_sync(self):
        get_scheduler().main(self)

    def on_start(self):
        """This is called once when the app is first launched"""
        if self.buttons:
            self.buttons.on_press(tidal.BUTTON_FRONT, lambda _: self.navigate_back())

    # Note: we don't actually stop apps yet...
    # def on_stop(self):
    #     return NotImplemented

    def on_activate(self):
        """This is called whenever the app is switched to the foreground"""
        if window := self.window:
            self.activate_window(window)
        else:
            window = ButtonOnlyWindow()
            window.buttons.on_press(tidal.BUTTON_FRONT, lambda _: self.navigate_back())
            self.push_window(window, activate=True)

    def on_deactivate(self):
        return NotImplemented

    def check_for_interrupts(self):
        if self.buttons:
            return self.buttons.check_for_interrupts()
        return False

    def navigate_back(self):
        get_scheduler().switch_app(None)

    def after(self, ms, callback):
        """Create a one-shot timer"""
        return get_scheduler().after(ms, callback)

    def periodic(self, ms, callback):
        """Create a periodic timer that fires repeatedly until cancel() is called on it"""
        return get_scheduler().periodic(ms, callback)

    @property
    def window(self):
        if len(self.windows):
            return self.windows[-1]
        else:
            return None
    
    @property
    def buttons(self):
        if window := self.window:
            return window.buttons
        else:
            return None
    
    def push_window(self, window, activate=True):
        self.windows.append(window)
        if activate:
            self.activate_window(window)

    def pop_window(self):
        self.deactivate_window(self.windows[-1])
        del self.windows[-1]
        if window := self.window:
            self.activate_window(window)

    def activate_window(self, window):
        if window.buttons:
            window.buttons.activate()
        window.redraw()

    def deactivate_window(self, window):
        if window.buttons:
            window.buttons.deactivate()


class ButtonOnlyWindow:
    """This class only exists to wrap a Buttons instance for any App which doesn't actually use a Window for drawing
       (and presumably draws directly to the display in its on_activate)
    """
    def __init__(self):
        self.buttons = Buttons()

    def redraw(self):
        pass


class TextApp(App):
    """An app using a single TextWindow by default"""

    def __init__(self):
        super().__init__()
        window = TextWindow(self.BG, self.FG, self.title, None, Buttons())
        self.push_window(window, activate=False)


class MenuApp(App):
    """An app using a single Menu window"""

    def __init__(self):
        super().__init__()
        window = Menu(self.BG, self.FG, self.FOCUS_BG, self.FOCUS_FG, self.title, self.choices, None, Buttons())
        self.push_window(window, activate=False)

    def on_start(self):
        super().on_start()
        win = self.window
        self.buttons.on_press(tidal.JOY_DOWN, lambda _: win.set_focus_idx(win.focus_idx() + 1))
        self.buttons.on_press(tidal.JOY_UP, lambda _: win.set_focus_idx(win.focus_idx() - 1))
        def select(_):
            if len(win.choices):
                win.choices[win.focus_idx()][1]()
        self.buttons.on_press(tidal.JOY_CENTRE, select, autorepeat=False)
        self.buttons.on_press(tidal.BUTTON_A, select, autorepeat=False)
        self.buttons.on_press(tidal.BUTTON_B, select, autorepeat=False)


class PagedApp(App):
    """An app that supports left/right switching between multiple page Windows"""

    PAGE_FOOTER = 7
    DOTS_SEP = 10

    def __init__(self):
        super().__init__()
        self._page = None

    def draw_dots(self):
        display = tidal.display
        y = display.height() - self.PAGE_FOOTER + 3
        n = len(self.pages)
        x = (display.width() - ((n - 1) * self.DOTS_SEP)) // 2
        for i in range(n):
            if i == self._page:
                display.fill_circle(x + (self.DOTS_SEP * i), y, 3, self.pages[i].fg)
            else:
                display.fill_circle(x + (self.DOTS_SEP * i), y, 1, self.pages[i].fg)

    def on_start(self):
        super().on_start()
        for i, page in enumerate(self.pages):
            if page.buttons is None:
                # Paged windows have to have a buttons so they can be navigated left and right
                page.buttons = Buttons()
            # Add our navigation buttons to whatever the page windows may have defined
            page.buttons.on_press(tidal.JOY_LEFT, lambda _: self.set_page(self.page - 1))
            page.buttons.on_press(tidal.JOY_RIGHT, lambda _: self.set_page(self.page + 1))
            page.buttons.on_press(tidal.BUTTON_FRONT, lambda _: self.navigate_back())

    @property
    def page(self):
        return self._page

    def set_page(self, val):
        self._page = val % len(self.pages)
        if self.window:
            self.pop_window()
        self.push_window(self.pages[self.page])
        self.draw_dots()

    def on_activate(self):
        super().on_activate()
        if self.page is None:
            self.set_page(0)
