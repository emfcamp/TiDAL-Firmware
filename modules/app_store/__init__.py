import tidal
import tidal_helpers
from app import MenuApp
from scheduler import get_scheduler
import term
import sys
import ujson
import os
import functools
import settings
from dashboard.resources import woezel_repo


class Store(MenuApp):

    APP_ID = "store"
    TITLE = "EMF 2022 - TiDAL"

    @property
    def choices(self):
        # Note, the text for each choice needs to be <= 16 characters in order to fit on screen
        choices = []
        return choices

    def progress(self, text, error=False, wifi=False):
        self.window.println(text)

    def on_start(self):
        super().on_start()
        woezel_repo.update(_showProgress=self.progress)
        self.data = woezel_repo.load()

    def on_activate(self):
        super().on_activate()
