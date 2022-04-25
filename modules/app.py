import tidal
import time
import uasyncio
from buttons import Buttons
import textwindow

class MainTask:
    
    _awaitables = {}
    _current_app = None
    
    async def sleep(self):
        # Sleep for 5 minutes, wrapped in an async funtion
        # so it can be scheduled as a cancellable task
        await uasyncio.sleep(300)
    
    async def app_active(self, app: str) -> bool:
        """Await this to pause execution until the specified app
        is active. Returns a boolean which is True if the app was active
        or False if we waited for it to become active. """
        # Infinite loop while the app is inactive, but with
        # a sleep in the middle so it doesn't use resources.
        was_already_active = self._current_app == app
        while self._current_app != app:
            task = self._awaitables.get(
                app,
                uasyncio.create_task(self.sleep())
            )
            self._awaitables[app] = task
            try:
                await task
            except:
                # We have context switched, swallow that CancelledError
                pass
            # Remove the awaitable, so it's re-created next time it's
            # requested
            del self._awaitables[app]
        return was_already_active
    
    def context_changed(self, app: str) -> None:
        # Cancel the corresponding sleep for this app, to wake it
        self._current_app = app
        print(f"Changing context to {app}")
        if awaitable := self._awaitables.get(app):
            awaitable.cancel()
        return


task_coordinator = MainTask()


class App:
    app_id = __name__
    running = True

    # Defaults for TextApp and MenuApp
    BG = tidal.BLUE
    FG = tidal.WHITE

    def __init__(self):
        self.buttons = Buttons()

    def run_sync(self):
        self.on_start()
        self.on_wake()
        # TODO sort this
        # time.sleep(self.post_wake_interval)
        # while self.running:
        #     self.update()
        #     time.sleep(self.interval)
        # self.on_stop()

    async def run(self):
        self.on_start()
        # TODO sort this
        self.on_wake()
        # first_run = True
        # while self.running:
        #     was_active = await task_coordinator.app_active(self.app_id)
        #     if first_run or not was_active:
        #         self.on_wake()
        #         first_run = False
        #         await uasyncio.sleep(self.post_wake_interval)
        #     self.update()
        #     await uasyncio.sleep(self.interval)
        # self.on_stop()
    
    async def isActive(self):
        while True:
            yield

    def on_start(self):
        self.buttons.on_press(tidal.BUTTON_FRONT, lambda _: self.navigate_back())

    def on_stop(self):
        return NotImplemented

    def on_wake(self):
        self.buttons.activate()

    def navigate_back(self):
        print("TODO go back to app launcher")

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

    def on_wake(self):
        self.window.cls()
        super().on_wake()
