import settings
import tidal
import tidal_helpers
import time
import uasyncio
import wifi

_scheduler = None

_FAR_FUTURE = const(2**63)

def get_scheduler():
    """Return the global scheduler object."""
    global _scheduler
    if not _scheduler:
        _scheduler = Scheduler()
    return _scheduler

class TimerTask:
    def __init__(self, fn, target_time, period_interval=None):
        self.scheduler = None
        self.target_time = target_time
        self.fn = fn
        self.period_interval = period_interval
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        if self.scheduler:
            self.scheduler._remove_timer_task(self)
            self.scheduler = None

    async def async_call(self):
        if self._cancelled:
            # Then the task was cancelled after it became ready to run
            return
        self.fn()

class Scheduler:
    _current_app = None
    _root_app = None
    sleep_enabled = True

    def __init__(self):
        self._timers = []
        self.no_sleep_before = time.ticks_ms() + (settings.get("boot_nosleep_time", 15) * 1000)
        self._wake_lcd_buttons = None
        self._current_backlight_val = None
        self._temp_wake_lcd = False
        self._deactivated_app = None

    def switch_app(self, app):
        """Asynchronously switch to the specified app."""
        uasyncio.create_task(self._switch_app(app))

    async def _switch_app(self, app):
        if app is None:
            app = self._root_app
        if app == self._current_app:
            # Nothing to do
            return
        # print(f"Switching app to {app.get_app_id()}")

        if not app.supports_rotation():
            current = tidal.get_display_rotation()
            if current == 90 or current == 270:
                tidal.set_display_rotation(0)

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

    def main(self, initial_app):
        """Main entry point to the scheduler. Does not return."""
        self._root_app = initial_app
        self.switch_app(initial_app)
        tidal_helpers.esp_sleep_enable_gpio_wakeup()
        self._level = 0
        self.reset_inactivity()
        self.enter()

    def enter(self):
        import accelerometer
        import magnetometer
        first_time = True
        self._level += 1
        enter_level = self._level
        deactivated_app = None
        while True:
            while self.check_for_interrupts() or first_time:
                first_time = False
                uasyncio.run_until_complete()

            if self._level < enter_level:
                break

            if cur := self._current_app:
                cur.on_tick()

            # Work out when we need to sleep until
            now = time.ticks_ms()
            lcd_sleep_time = self._last_activity_time + self.get_inactivity_time()
            should_sleep_lcd = (lcd_sleep_time <= now) and not self._temp_wake_lcd
            can_sleep = self.can_sleep()
            if can_sleep and should_sleep_lcd:
                # Then we have to notify the app that we're going to switch off
                # the LCD, which might alter the next timer wakeup if the app
                # has timers it cancels in its on_deactivate(), hence why we do
                # this before calling peek_timer()
                deactivated_app = self._current_app
                if deactivated_app:
                    self._deactivated_app = deactivated_app
                    deactivated_app.on_deactivate()

            if next_timer_task := self.peek_timer():
                next_time = next_timer_task.target_time
            else:
                next_time = _FAR_FUTURE

            # Force a wake when the screen is due to switch off
            if now < lcd_sleep_time:
                next_time = min(next_time, lcd_sleep_time)

            if next_time <= now:
                # Oops we missed a timer, continue to go back to check_for_interrupts() at top of loop
                continue
            elif next_time == _FAR_FUTURE:
                t = 0
            else:
                t = next_time - now

            if can_sleep:
                # print(f"Sleepy time {t} should_sleep_lcd={should_sleep_lcd}")
                if should_sleep_lcd:
                    self.set_backlight_value(None)
                    tidal.lcd_power_off()
                    # Switch buttons so that (a) a press while the screen is off
                    # doesn't get passed to the app, and (b) so that any button
                    # wakes the screen, even ones the app hasn't registered an
                    # interrupt for.
                    self.wake_lcd_buttons.activate()

                    # Other power management actions we want to do before display off
                    accelerometer.sleep()
                    magnetometer.sleep()

                # Make sure any debug prints show up on the UART
                tidal_helpers.uart_tx_flush(0)

                wakeup_cause = tidal_helpers.lightsleep(t)
                # print(f"Returned from lightsleep reason={wakeup_cause}")

                # deactivated_app's buttons will be reactivated from reset_inactivity
            else:
                if t == 0:
                    # Add a bit of a sleep (which uses less power than straight-up looping)
                    t = 100
                # Don't sleep for more than 0.1s otherwise buttons will be unresponsive
                time.sleep(min(0.1, t / 1000))

    def exit(self):
        self._level = self._level - 1

    def set_sleep_enabled(self, flag):
        print(f"Light sleep enabled: {flag}")
        self.sleep_enabled = flag

    def is_sleep_enabled(self):
        return self.sleep_enabled

    def can_sleep(self):
        return (
            self.sleep_enabled and
            tidal_helpers.get_variant() != "devboard" and
            not tidal_helpers.usb_connected() and
            not wifi.active() and
            time.ticks_ms() >= self.no_sleep_before
        )

    def reset_inactivity(self):
        # print("Reset inactivity")
        if self._temp_wake_lcd:
            if tidal._LCD_BLEN.value() == 0:
                # print("Ignoring reset inactivity while backlight button is down")
                pass
            else:
                # print("Unsetting _temp_wake_lcd")
                self._temp_wake_lcd = False
            return

        if self.wake_lcd_buttons.is_active():
            # Make sure we stop anything involving the backlight pin prior to potentially reconfiguring it
            self.wake_lcd_buttons.deactivate()

        if self._deactivated_app:
            # This will also reactivate its buttons
            # print("Reactivating previous app")
            self._deactivated_app.on_activate()
            self._deactivated_app = None

        self._last_activity_time = time.ticks_ms()
        if not tidal.lcd_is_on():
            tidal.lcd_power_on()
        # Restore backlight setting if necessary
        self.set_backlight_value(settings.get("backlight_pwm"))

    def set_backlight_value(self, backlight_val):
        # don't reconfigure PWM unless necessary, as this restarts the PWM
        # waveform causing a potential slight flicker.
        if backlight_val != self._current_backlight_val:
            self._current_backlight_val = backlight_val
            tidal_helpers.set_backlight_pwm(tidal._LCD_BLEN, backlight_val)

    @property
    def wake_lcd_buttons(self):
        if self._wake_lcd_buttons is None:
            import buttons
            self._wake_lcd_buttons = buttons.Buttons()
            for button in tidal.ALL_BUTTONS:
                # We don't need these button presses to do anything, they just have to exist
                self._wake_lcd_buttons.on_press(button, lambda: 0)
            self._wake_lcd_buttons.on_up_down(tidal._LCD_BLEN, self.backlight_button_pressed)
        return self._wake_lcd_buttons

    def usb_plug_event(self, charging):
        # print(f"CHARGE_DET charging={charging}")
        if charging:
            # Prevent sleep again to give USB chance to enumerate
            self.no_sleep_before = time.ticks_ms() + (settings.get("usb_nosleep_time", 15) * 1000)

    def backlight_button_pressed(self, pressed):
        if pressed:
            self._temp_wake_lcd = True
            # print("LCD temp wake")
            tidal.display.sleep_mode(0)
        else:
            # Don't clear _temp_wake_lcd here, it has to be done after the reset_inactivity from
            # Buttons.check_buttons(). Yes this has become uglier than I'd like...
            # print("LCD resleep")
            tidal.display.sleep_mode(1)

    def get_inactivity_time(self):
        return settings.get("inactivity_time", 30) * 1000

    def check_for_interrupts(self):
        """Check for any pending interrupts and schedule uasyncio tasks for them."""
        found = self.wake_lcd_buttons.check_for_interrupts()
        if self._current_app and self._current_app.check_for_interrupts():
            found = True
        t = time.ticks_ms()
        while True:
            task = self.peek_timer()
            if task and task.target_time <= t:
                # print(f"Timer ready at {task.target_time}")
                found = True
                del self._timers[0]
                task.scheduler = None
                uasyncio.create_task(task.async_call())
                if task.period_interval:
                    # Re-add the task with an updated target time
                    task.target_time = task.target_time + task.period_interval
                    self.add_timer_task(task)
                continue # Check next timer in the queue
            else:
                break

        return found

    def add_timer_task(self, task):
        self._timers.append(task)
        task.scheduler = self
        self._timers.sort(key=lambda t: t.target_time)

    def _remove_timer_task(self, task):
        self._timers.remove(task)

    def peek_timer(self):
        if len(self._timers) > 0:
            return self._timers[0]
        else:
            return None

    def after(self, ms, callback):
        task = TimerTask(callback, time.ticks_ms() + ms)
        self.add_timer_task(task)
        return task

    def periodic(self, ms, callback):
        task = TimerTask(callback, time.ticks_ms() + ms, ms)
        self.add_timer_task(task)
        return task
