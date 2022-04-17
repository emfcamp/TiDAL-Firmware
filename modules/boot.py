import _thread
from bootmenu import show_boot_menu


# TODO: figure out how to get show_boot_menu to use callbacks and become async
# so it needn't be wrapped in a thread to prevent it blocking the serial/USB
# REPL.
_thread.start_new_thread(show_boot_menu, ())
