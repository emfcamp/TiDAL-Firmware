import tidal
import tidal_helpers
from app import MenuApp
from buttons import Buttons
from textwindow import Menu
from scheduler import get_scheduler
import time
import term
import sys
import ujson
import os
import functools
import settings
import authenticator

def path_isfile(path):
    # Wow totally an elegant way to do os.path.isfile...
    try:
        return (os.stat(path)[0] & 0x8000) != 0
    except:
        return False

def path_isdir(path):
    try:
        return (os.stat(path)[0] & 0x4000) != 0
    except:
        return False

def recursive_delete(path):
    contents = os.listdir(path)
    for name in contents:
        entry_path = f"{path}/{name}"
        if path_isdir(entry_path):
            recursive_delete(entry_path)
        else:
            os.remove(entry_path)
    os.rmdir(path)

class Launcher(MenuApp):

    APP_ID = "menu"
    TITLE = "EMF 2022 - TiDAL"

    def loadInfo(self, folder, name):
        try:
            info_file = "{}/{}/metadata.json".format(folder, name)
            with open(info_file) as f:
                information = f.read()
            return ujson.loads(information)
        except BaseException as e:
            return {}

    def list_user_apps(self):
        ticks = time.ticks_ms()
        apps = []
        app_dir = "/apps"
        try:
            contents = os.listdir(app_dir)
        except OSError:
            # No apps dir full stop
            return []

        for name in contents:
            if not path_isfile(f"{app_dir}/{name}/__init__.py"):
                continue
            app = {
                "path": name,
                "callable": "main",
                "name": name,
                "icon": None,
                "category": "unknown",
                "hidden": False,
            }
            metadata = self.loadInfo(app_dir, name)
            app.update(metadata)
            if not app["hidden"]:
                apps.append(app)
        elapsed = (time.ticks_ms() - ticks) / 1000
        print(f"list_user_apps took {elapsed:0.1f}s")
        return apps

    def list_core_apps(self):
        core_app_info = [
            ("App store", "app_store", "Store"),
            ("USB Keyboard", "hid", "USBKeyboard"),
            ("Authenticator", "authenticator", "Authenticator"),
            ("Name Badge", "hello", "Hello"),
            ("Torch", "torch", "Torch"),
            ("Logo", "emflogo", "EMFLogo"),
            ("Update Firmware", "otaupdate", "OtaUpdate"),
            ("Wi-Fi Connect", "wifi_client", "WifiClient"),
            ("Sponsors", "sponsors", "Sponsors"),
            ("Battery", "battery", "Battery"),
            ("Accelerometer", "accel_app", "Accel"),
            ("Magnetometer", "magnet_app", "Magnetometer"),
            ("Settings", "settings_app", "SettingsApp"),
            # ("Swatch", "swatch", "Swatch"),
            # ("uGUI Demo", "ugui_demo", "uGUIDemo")
        ]
        core_apps = []
        for core_app in core_app_info:
            core_apps.append({
                "path": core_app[1],
                "callable": core_app[2],
                "name": core_app[0],
                "icon": None,
                "category": "unknown",
            })
        return core_apps

    @property
    def choices(self):
        # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
        user_apps = self.list_user_apps()
        apps = self.list_core_apps() + user_apps
        choices = []
        for app in apps:
            choices.append((app['name'], functools.partial(self.launch, app['path'], app['callable'])))
        if len(user_apps) > 0:
            choices.append(("Uninstall...", self.show_uninstall))
        return choices

    # Boot entry point
    def main(self):
        sys.path[0:0] = ["/apps"]

        if settings.get("uart_menu_app", True):
            # Then we run ourselves in a thread and let the terminal be the main thread
            import _thread
            import tidal
            _thread.stack_size(16 * 1024)
            menu_thread = _thread.start_new_thread(get_scheduler().main, (self,))

            from term_menu import UartMenu
            term_menu = UartMenu(gts=tidal.system_power_off, pm=None)
            term_menu.main()
        else:
            # Run directly
            get_scheduler().main(self)

    def as_terminal_app(self):
        while True:
            term.clear()
            choice = term.menu(
                self.window.title.replace("\n", " "),
                [text for (text, cb) in self.choices]
            )
            self.choices[choice][1]()

    def __init__(self):
        super().__init__()
        self._apps = {}
        self.first_run_first_activate = not settings.get("first_run_done", False)

    def on_start(self):
        super().on_start()
        self.window.set_choices(self.choices, redraw=False)
        self.buttons.on_press(tidal.BUTTON_FRONT, self.refresh)

        initial_item = 0
        try:
            with open("/lastapplaunch.txt") as f:
                initial_item = int(f.read())
        except:
            pass
        self.window.set_focus_idx(initial_item, redraw=False)

    def on_activate(self):
        if self.first_run_first_activate:
            self.first_run_first_activate = False
            import sponsors
            get_scheduler().switch_app(sponsors.Sponsors())
            return

        # Don't set this until here, it can result in spurious redraws if setup
        # in on_start or prior to the first_run_first_activate check
        self.buttons.on_up_down(tidal.CHARGE_DET, self.charge_state_changed)

        self.update_title(redraw=False)
        self.window.set_choices(self.choices, False)
        super().on_activate()

    def update_title(self, redraw):
        title = self.TITLE
        if not get_scheduler().is_sleep_enabled():
            title += "\nSLEEP DISABLED"
        pwr = tidal.CHARGE_DET.value() == 0 and 1 or 0
        conn = (tidal_helpers.usb_connected() and not tidal_helpers.usb_suspended()) and 1 or 0
        if pwr or conn:
            title += f"\nUSB pwr={pwr} conn={conn}"
        if title != self.window.title:
            self.window.set_title(title, redraw=redraw)

    def launch(self, module_name, fn):
        app_id = f"{module_name}.{fn}"
        app = self._apps.get(app_id)
        if app is None:
            print(f"Creating app {app_id}...")
            module = __import__(module_name, None, None, (fn,))
            app = getattr(module, fn)()
            self._apps[app_id] = app
        with open("/lastapplaunch.txt", "w") as f:
            f.write(str(self.window.focus_idx()))
        get_scheduler().switch_app(app)

    def charge_state_changed(self, charging):
        self.update_title(redraw=True)
        get_scheduler().usb_plug_event(charging)

    def refresh(self):
        self.update_title(redraw=False)
        self.window.set_choices(self.choices, redraw=False)
        self.window.redraw()

    def show_uninstall(self):
        menu = UninstallMenu(self)
        self.push_window(menu)


class UninstallMenu(Menu):
    def __init__(self, launcher):
        buttons = Buttons()
        buttons.on_press(tidal.BUTTON_FRONT, self.pop, autorepeat=False)
        root = launcher.window
        super().__init__(root.bg, root.fg, root.focus_bg, root.focus_fg, "Select an app to\nuninstall", [], None, buttons)
        self.launcher = launcher

    def pop(self):
        self.launcher.pop_window()
        self.launcher.refresh()

    def redraw(self):
        choices = []
        user_apps = self.launcher.list_user_apps()
        for app in user_apps:
            choices.append((app["name"], functools.partial(self.uninstall, app)))
        if len(user_apps) == 0:
            choices.append(("<No more apps>", lambda: 0))
        self.set_choices(choices, redraw=False)
        super().redraw()

    def uninstall(self, app):
        ret = self.launcher.yes_no_prompt("Really\nuninstall?")
        if ret:
            print(f"Uninstalling {app['name']}")
            recursive_delete(f"/apps/{app['path']}")
            self.redraw()
