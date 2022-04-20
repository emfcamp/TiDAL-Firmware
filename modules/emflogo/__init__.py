from tidal import *
import emf_png
import time

def main():
    display.vscrdef(40, 240, 40)
    display.vscsad(40)
    display.bitmap(emf_png, 0, 0)
    i = 0
    while True:
        i = i + 1
        if i >= 240:
            i = 0
        display.vscsad(40 + i)
        time.sleep(0.01)
