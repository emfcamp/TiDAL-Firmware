import tidal_helpers
import time
import uasyncio

_scheduler = None

def get_scheduler():
    global _scheduler
    if not _scheduler:
        _scheduler = Scheduler()
    return _scheduler

class TimerTask:
    def __init__(self, main_task, fn, time_ticks, period_interval=None):
        self.main_task = main_task
        self.time_ticks = time_ticks
        self.fn = fn
        self.period_interval = period_interval

    def cancel(self):
        self.main_task.cancel_task(self)

    async def async_call(self):
        self.fn()

class Scheduler:
    
    _current_app = None
    _root_app = None
    sleep_enabled = True

    def __init__(self):
        self._timers = []
    
    def switch_app(self, app):
        uasyncio.create_task(self._switch_app(app))

    async def _switch_app(self, app):
        if app is None:
            app = self._root_app
        if app == self._current_app:
            # Nothing to do
            return
        print(f"Switching app to {app.app_id}")

        if app.buttons:
            app.buttons.activate()
        elif self._current_app and self._current_app.buttons:
            # Then we'd better at least deactivate the current buttons
            self._current_app.buttons.deactivate()

        if self._current_app:
            self._current_app.on_deactivate()

        self._current_app = app
        if not app.started:
            app.started = True
            app.on_start()
        app.on_activate()

    def get_next_sleep_time(self):
        next_timer_task = self.peek_timer()
        if next_timer_task:
            next_time = next_timer_task.time_ticks
            return max(1, next_time - time.ticks_ms())
        else:
            return 0

    def main(self, initial_app):
        self._root_app = initial_app
        self.switch_app(initial_app)
        tidal_helpers.esp_sleep_enable_gpio_wakeup()
        first_time = True
        while True:
            while self.check_for_interrupts() or first_time:
                first_time = False
                uasyncio.run_until_complete()

            if self.sleep_enabled:
                t = self.get_next_sleep_time()
                # print(f"Sleepy time {t}")
                # Make sure any debug prints show up on the USB UART
                tidal_helpers.uart_tx_flush(0)
                wakeup_cause = tidal_helpers.lightsleep(t)
                # print(f"Returned from lightsleep reason={wakeup_cause}")
            else:
                # Just spin
                pass


    def check_for_interrupts(self):
        found = False
        if self._current_app and self._current_app.check_for_interrupts():
            found = True
        t = time.ticks_ms()
        while True:
            task = self.peek_timer()
            if task and task.time_ticks <= t:
                # print(f"Timer ready at {task.time_ticks}")
                found = True
                del self._timers[0]
                uasyncio.create_task(task.async_call())
                if task.period_interval:
                    task.time_ticks = task.time_ticks + task.period_interval
                    self.add_timer_task(task)
                continue # Check next timer in the queue
            else:
                break

        return found

    def add_timer_task(self, task):
        self._timers.append(task)
        self._timers.sort(key=lambda t: t.time_ticks)

    def cancel_task(self, task):
        self._timers.remove(task)

    def peek_timer(self):
        if len(self._timers) > 0:
            return self._timers[0]
        else:
            return None

    def after(self, ms, callback):
        task = TimerTask(self, callback, time.ticks_ms() + ms)
        self.add_timer_task(task)
        return task

    def periodic(self, ms, callback):
        task = TimerTask(self, callback, time.ticks_ms() + ms, ms)
        self.add_timer_task(task)
        return task
