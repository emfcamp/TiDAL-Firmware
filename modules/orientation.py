import consts, machine, tidal, buttons

def default(rotateButtons=True):
    value = consts.DEFAULT_ORIENTATION
    if rotateButtons:
        buttons.rotate(value)
    tidal.set_display_rotation(value)

def landscape(rotateButtons=True):
    if rotateButtons:
        buttons.rotate(90)
    tidal.set_display_rotation(90)

def portrait(rotateButtons=True):
    if rotateButtons:
        buttons.rotate(0)
    tidal.set_display_rotation(0)

def isLandscape(value=None):
    if value == None:
        value = tidal.get_display_rotation()
    if value==90 or value==270:
        return True
    return False

def isPortrait(value=None):
    if value == None:
        value = tidal.get_display_rotation()
    if value==90 or value==270:
        return False
    return True
