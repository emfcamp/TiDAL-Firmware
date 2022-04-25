import st7789
import tidal
from app import MenuApp, task_coordinator
import uasyncio


class Launcher(MenuApp):

    app_id = "menu"
    title = "EMF 2022 - TiDAL\nBoot Menu"
    BG = st7789.BLUE
    FG = st7789.WHITE
    FOCUS_FG = st7789.BLACK
    FOCUS_BG = st7789.CYAN
    to_launch = None
    apps = {}

    @property
    def choices(self):
        # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
        return (
            ({"text": "USB Keyboard"}, lambda: self.launch("hid", "USBKeyboard")),
            ({"text": "Web REPL"}, lambda: self.launch("web_repl", "WebRepl")),
            ({"text": "Torch"}, lambda: self.launch("torch", "Torch")),
            ({"text": "Logo"}, lambda: self.launch("emflogo", "EMFLogo")),
            ({"text": "Update Firmware"}, lambda: self.launch("otaupdate", "OtaUpdate")),
        )
    
    async def run(self):
        self.on_start()
        self.on_wake() #TODO sort this out
        # first_run = True
        # while self.running:
        #     was_active = await task_coordinator.app_active(self.app_id)
        #     if first_run or not was_active:
        #         self.on_wake()
        #         first_run = False
        #         await uasyncio.sleep(self.post_wake_interval)
        #     self.update()
        #     if self.to_launch:
        #         to_launch = self.to_launch
        #         self.to_launch = None
        #         app = self.apps.get(to_launch)
        #         if app is None or not app.running:
        #             module = __import__(to_launch[0])
        #             app = getattr(module, to_launch[1])()
        #             self.apps[to_launch] = app
        #             uasyncio.create_task(app.run())
        #             task_coordinator.context_changed(app.app_id)
        #     await uasyncio.sleep(self.interval)
        # self.on_stop()
    
    def launch(self, module_name, app_name):
        # self.to_launch = module, app
        # TODO fix this
        self.buttons.deactivate()
        module = __import__(module_name)
        app = getattr(module, app_name)()
        app.on_start()
        app.on_wake()
