from textwindow import TextWindow
import tidal

_msg_window = None

def showMessage(message):
    global _msg_window
    if _msg_window is None:
        _msg_window = TextWindow(bg=tidal.RED, fg=tidal.WHITE, title="Serial App")
    _msg_window.cls()
    for line in _msg_window.flow_lines(message):
        _msg_window.println(line)

def serialWarning():
	showMessage("App is running\nover USB Serial\nport.")
	
def crashedWarning():
	showMessage("FATAL ERROR\nthe app has crashed")
