import _thread
import joystick

_thread.start_new_thread(joystick.joystick_active, ())
