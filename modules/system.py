from textwindow import TextWindow
import tidal


def showMessage(message):
    window = TextWindow(bg=tidal.RED)
    window.cls()
    x = 0
    while x < len(message):
        window.println(message[x:x+16])
        x += 16

def serialWarning():
	showMessage("This app can only be controlled using the USB serial port!")
	
def crashedWarning():
	showMessage("FATAL ERROR\nthe app has crashed")
