import term, orientation, system, time, consts, term_menu

def getOrientationString(currentValue):
    orientationString = str(currentValue)
    if currentValue == 0:
        orientationString = "Portrait"
    if currentValue == 90:
        orientationString = "Landscape"
    if currentValue == 180:
        orientationString = "Portrait inverted"
    if currentValue == 270:
        orientationString = "Landscape inverted"
    return orientationString

items = ["Default", "Landscape", "Portrait", "Landscape inverted", "Portrait inverted", "< Back"]
options = [consts.DEFAULT_ORIENTATION, 0, 90, 180, 270, -1, -1]
currentValue = consts.DEFAULT_ORIENTATION
orientationString = getOrientationString(currentValue)
message = "Current orientation: "+orientationString+"\n"
newValue = options[term.menu("Configure orientation", items, 0, message)]
if newValue < 0:
    system.home(True)
term.header(True, "Configure orientation")

time.sleep(1)
term_menu.return_to_home()