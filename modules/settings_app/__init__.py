import tidal
from app import MenuApp
from buttons import Buttons
from scheduler import get_scheduler
import settings
from textwindow import Menu
import wifi

class SettingsMenu(Menu):
    """Like Menu but supporting 2 lines per item with the 2nd right-aligned"""

    def get_max_items(self):
        return self.get_max_lines() // 2

    def draw_item(self, index, focus):
        text = self.choices[index][0].split("\n")
        while len(text) < 2:
            text.append("")

        # TODO support top and bottom scroll arrows if we ever get that many settings

        text[1] = (" " * (self.width_chars() - len(text[1]))) + text[1]

        fg = self.focus_fg if focus else self.fg
        bg = self.focus_bg if focus else self.bg

        line_pos = (index - self._top_idx) * 2
        self.println(text[0], line_pos, fg, bg)
        self.println(text[1], line_pos + 1, fg, bg)

    def draw_items(self):
        for i in range(self._top_idx, self._end_idx):
            self.draw_item(i, i == self._focus_idx)
        self.clear_from_line((self._end_idx - self._top_idx) * 2)


# Yes there must be eleventy million versions of this function out there. This is good enough though.
def fmt_time(val):
    if val < 60:
        return f"{val} seconds"
    elif val % (60*60) == 0:
        return f"{val // (60*60)} hours"
    elif val % 60 == 0:
        return f"{val // 60} minutes"

    parts = []
    if val >= 60*60:
        hours = val // (60*60)
        val = val - (hours * 60*60)
        parts.append(f"{hours}h")
    if val >= 60:
        mins = val // 60
        val = val - (mins * 60)
        parts.append(f"{mins}m")
    if val > 0:
        parts.append(f"{val}s")

    return " ".join(parts)

def fmt_wifi_dbm(val):
    if val <= 8:
        return "2 dBm"
    elif val <= 20:
        return "5 dBm"
    elif val <= 28:
        return "7 dBm"
    elif val <= 34:
        return "8 dBm"
    elif val <= 44:
        return "11 dBm"
    elif val <= 52:
        return "13 dBm"
    elif val <= 56:
        return "14 dBm"
    elif val <= 60:
        return "15 dBm"
    elif val <= 66:
        return "16 dBm"
    elif val <= 72:
        return "18 dBm"
    elif val <= 80:
        return "20 dBm"
    else:
        return f"??{val}??"

def no_fmt(val):
    return str(val)

class SettingsApp(MenuApp):

    TITLE = "Settings"

    def __init__(self):
        window = SettingsMenu(self.BG, self.FG, self.FOCUS_BG, self.FOCUS_FG, self.TITLE, self.CHOICES, self.FONT, Buttons())
        super().__init__(window)

    def supports_rotation(self):
        return False # It kinda looks bad in landscape...

    def on_start(self):
        super().on_start()

    def on_activate(self):
        super().on_activate()
        self.refresh()

    def on_deactivate(self):
        # The simplistic way this app is structured, there's no good way to
        # redraw a make_choice window when we reactivate (eg with updated values
        # if necessary) so instead just pop back to the root window here
        while len(self.windows) > 1:
            self.pop_window()
        super().on_deactivate()

    def refresh(self):
        choices = (
            self.make_choice("Display sleep", None, "inactivity_time", get_scheduler().get_inactivity_time(), fmt_time,
                (5, 15, 30, 60, 5*60, 10*60, 30*60)),
            self.make_choice("WiFi TX power", None, "wifi_tx_power", wifi.DEFAULT_TX_POWER, fmt_wifi_dbm, (8, 20, 28, 34)),
            self.make_choice("WiFi con timeout", "WiFi connection\ntimeout", "wifi_connection_timeout",
                wifi.DEFAULT_CONNECT_TIMEOUT, fmt_time, (10, 20, 30, 60, 120)),
            self.make_choice("Boot sleep delay", None, "boot_nosleep_time", 15, fmt_time,
                (5, 15, 30, 60, 5*60, 10*60, 30*60, 60*60, 8*60*60)),
            self.make_choice("USB sleep delay", None, "usb_nosleep_time", 15, fmt_time, (15, 30, 60)),
        )
        self.window.set_choices(choices)

    def make_choice(self, title, long_title, name, default, fmt, choices):
        text = f"{title}\n{fmt(settings.get(name, default))}"
        def fn():
            items = []
            idx = 0
            current_val = settings.get(name, default)
            for i, val in enumerate(choices):
                if val == current_val:
                    idx = i
                items.append((fmt(val), self.make_setparam_fn(name, val)))
            menu = Menu(self.BG, self.FG, self.FOCUS_BG, self.FOCUS_FG, long_title or title, items, self.FONT, Buttons())
            menu.set_focus_idx(idx, redraw=False)
            menu.buttons.on_press(tidal.BUTTON_FRONT, lambda: self.pop_window(), autorepeat=False)
            self.push_window(menu)
        return (text, fn)

    def make_setparam_fn(self, name, value):
        # I hate Python variable capture rules so much...
        def fn():
            settings.set(name, value)
            settings.save()
            self.pop_window()
            self.refresh()
        return fn
