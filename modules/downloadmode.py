from tidal import *
import textwindow
from tidal_helpers import reboot_bootloader

# Note, this intentionally doesn't inherit App or TextApp to limit dependencies
# because it is on the critical path from the Recovery Menu.
# But it acts sufficiently like it does, to satisfy the app launcher
class DownloadMode:
    
    title = "USB Download"
    
    BG = MAGENTA
    FG = WHITE


    def run_sync(self):
        self.on_start()
        self.on_activate()

    def get_app_id(self):
        return "downloadmode"

    def on_start(self):
        self.window = textwindow.TextWindow(self.BG, self.FG, self.title)

    def on_activate(self):
        window = self.window
        window.cls()

        window.println("Now in download mode")
        window.println("Plug TiDAL in")
        reboot_bootloader()
