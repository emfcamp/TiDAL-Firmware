import tidal
from buttons import Buttons
from scheduler import get_scheduler
from textwindow import TextWindow, Menu
from keyboard import Keyboard

class App:

    def __init__(self):
        self.started = False
        self.windows = []
        self._is_active = False

    def get_app_id(self):
        if name := getattr(self, "APP_ID", None):
            return name
        else:
            return self.__class__.__name__

    def run_sync(self):
        get_scheduler().main(self)

    def on_start(self):
        """This is called once when the app is first launched"""
        if self.buttons:
            self.buttons.on_press(tidal.BUTTON_FRONT, self.navigate_back, autorepeat=False)
            if self.supports_rotation():
                self.buttons.on_press(tidal.BUTTON_B, self.rotate)
            else:
                self.buttons.on_press(tidal.BUTTON_B, self.flip)

    # Note: we don't actually stop apps yet...
    # def on_stop(self):
    #     return NotImplemented

    def on_activate(self):
        """This is called whenever the app is switched to the foreground"""
        self._is_active = True
        self.set_rotation(tidal.get_display_rotation(), redraw=False) # Resync this if necessary
        if window := self.window:
            self._activate_window(window)
        else:
            window = ButtonOnlyWindow()
            window.buttons.on_press(tidal.BUTTON_FRONT, self.navigate_back, autorepeat=False)
            self.push_window(window, activate=True)

    def on_deactivate(self):
        self._is_active = False

    def is_active(self):
        """Returns True if the app is currently in the foreground """
        return self._is_active

    def check_for_interrupts(self):
        if self.buttons:
            return self.buttons.check_for_interrupts()
        return False

    def supports_rotation(self):
        """Override this to allow the app to open in landscape and to default BUTTON_B to rotate"""
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
            self._activate_window(window)

    def pop_window(self):
        self._deactivate_window(self.windows[-1])
        del self.windows[-1]
        if window := self.window:
            self._activate_window(window)

    def present_window(self, window):
        """Pushes window, and does not return until finish_presenting() is called"""
        self.push_window(window)
        get_scheduler().enter()
        self.pop_window()

    def finish_presenting(self):
        get_scheduler().exit()

    def keyboard_prompt(self, prompt, initial_value="", multiline_allowed=False):
        """Prompts the user to enter a value using the onscreen keyboard"""
        result = [initial_value]
        def completion(val):
            result[0] = val
            self.finish_presenting()
        keyboard = Keyboard(completion, prompt, initial_value, multiline_allowed)
        self.present_window(keyboard) # Doesn't return until all finished
        return result[0]

    def set_window(self, new_window, activate=True):
        if len(self.windows):
            self.windows[-1] = new_window
            if activate:
                self._activate_window(new_window)
        else:
            self.push_window(new_window, activate=activate)

    def _activate_window(self, window):
        if window.buttons:
            window.buttons.activate()
        window.redraw()

    def _deactivate_window(self, window):
        if window.buttons:
            window.buttons.deactivate()

    def get_rotation(self):
        return tidal.get_display_rotation()

    def set_rotation(self, rotation, redraw=True):
        if buttons := self.buttons:
            buttons.set_rotation(rotation)
        tidal.set_display_rotation(rotation)
        if redraw and self.window:
            self.window.redraw()

    def rotate(self):
        self.set_rotation((self.get_rotation() + 90) % 360)

    def flip(self):
        self.set_rotation((self.get_rotation() + 180) % 360)


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

    BG = None
    FG = None
    TITLE = None
    FONT = None

    def __init__(self):
        super().__init__()
        window = TextWindow(self.BG, self.FG, self.TITLE, self.FONT, Buttons())
        self.push_window(window, activate=False)


class MenuApp(App):
    """An app using a single Menu window"""

    BG = None
    FG = None
    FOCUS_FG = None
    FOCUS_BG = None
    TITLE = None
    FONT = None
    CHOICES = ()

    def __init__(self, window=None):
        super().__init__()
        if not window:
            window = Menu(self.BG, self.FG, self.FOCUS_BG, self.FOCUS_FG, self.TITLE, self.CHOICES, self.FONT, Buttons())
        self.push_window(window, activate=False)

    def supports_rotation(self):
        return True


class PagedApp(App):
    """An app that supports left/right switching between multiple page Windows"""

    PAGE_FOOTER = 7
    DOTS_SEP = 10

    def __init__(self):
        super().__init__()
        self._page = 0

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
            page.buttons.on_press(tidal.JOY_LEFT, lambda: self.set_page(self.page - 1))
            page.buttons.on_press(tidal.JOY_RIGHT, lambda: self.set_page(self.page + 1))
            page.buttons.on_press(tidal.BUTTON_FRONT, self.navigate_back, autorepeat=False)
        self.push_window(self.pages[self.page], activate=False)

    @property
    def page(self):
        return self._page

    def set_page(self, val):
        self._page = val % len(self.pages)
        self.set_window(self.pages[self.page])
        self.draw_dots()

    def on_activate(self):
        super().on_activate()
        self.draw_dots()
