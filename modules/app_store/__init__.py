from app import MenuApp, Menu
from buttons import Buttons
from textwindow import TextWindow
from scheduler import get_scheduler
import time
import tidal
from dashboard.resources import woezel_repo
import woezel


class UpdateProgress(TextWindow):

    def progress(self, text, error=False, wifi=False):
        for line in self.flow_lines(text):
            if error:
                self.println(line, fg=tidal.WHITE, bg=tidal.ADDITIONAL_RED)
            elif wifi:
                self.println(line, fg=tidal.BRAND_CYAN)
            else:
                self.println(line)

    def redraw(self):
        super().redraw()
        if not woezel_repo.load():
            try:
                woezel_repo.update(_showProgress=self.progress)
            except OSError:
                pass
            time.sleep(0.5)
        self.return_back()

class InstallProgress(TextWindow):

    def redraw(self):
        self.cls()
        self.println("Installing...")
        

class AppList(Menu):
    
    def __init__(self, title, slug, bg, fg, focus_bg, focus_fg, font, buttons, push_window, pop_window):
        self.category = slug
        self.push_window = push_window
        self.pop_window = pop_window
        super().__init__(bg, fg, focus_bg, focus_fg, title, self._choices, font, buttons)
    
    def return_back(self):
        self.pop_window()
        self.redraw()
    
    def installer(self, slug):
        print(f"Install option for {slug}")
        def do_install():
            print(f"installing {slug}")
            progress = InstallProgress(self.return_back)
            progress.bg = self.bg
            progress.fg = self.fg
            self.push_window(progress)
            woezel.install(slug)
            self.pop_window()
        return do_install    
    
    def make_choice(self, item):
        return item['name'], self.installer(item['slug'])
    
    @property
    def _choices(self):
        return [
            self.make_choice(application)
            for application in woezel_repo.getCategory(self.category)
        ]

class Store(MenuApp):
    APP_ID = "store"
    TITLE = "App store"

    @property
    def choices(self):
        # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
        choices = [self.make_choice(choice) for choice in woezel_repo.categories]
        return choices

    def make_choice(self, choice):
        return (choice['name'], self.launch_app_list(choice))

    def launch_app_list(self, choice):
        def do_launch():
            sub_buttons = Buttons()
            sub_buttons.on_press(tidal.BUTTON_FRONT, self.return_back, autorepeat=False)
            menu = AppList(
                choice['name'],
                choice['slug'],
                self.window.bg,
                self.window.fg,
                self.window.focus_bg,
                self.window.focus_fg,
                self.window.font,
                sub_buttons,
                self.push_window,
                self.pop_window
            )
            print(f"Pushing {menu}")
            self.push_window(menu)
        return do_launch

    def on_activate(self):
        super().on_activate()
        update = UpdateProgress(buttons=Buttons())
        update.buttons.on_press(tidal.BUTTON_FRONT, self.pop_window, autorepeat=False)
        update.return_back = self.return_back
        self.push_window(update)

    def return_back(self):
        self.pop_window()
        self.refresh()

    def refresh(self):
        self.window.set_choices(self.choices)