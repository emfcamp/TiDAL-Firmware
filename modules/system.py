from textwindow import TextWindow
import tidal


def showMessage(message):
    window = TextWindow(bg=tidal.RED)
    window.cls()
    for line in window.flow_lines(message):
        window.println(line)

def serialWarning():
	showMessage("This app can only be controlled using the USB serial port!")
	
def crashedWarning():
	showMessage("FATAL ERROR\nthe app has crashed")
