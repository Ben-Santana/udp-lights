# Defines effect functions strip[] -> strip[] modifies alpha values
import time
import math
from config.effects import *

# idle
def idleEffect(strip):
    return strip

# sin
def sinWave(strip, bpm=default_bpm * 2, wave_length=3):
    new_strip = strip

    for i in range(len(new_strip)):
        new_strip[i][3] = (math.sin(2 * math.pi * (time.time() / 60) * bpm + i / wave_length) + 1)/2 * 255

    return new_strip

# chase
def chase(strip, bpm=default_bpm, length=10, lifetime = 0.5):
    new_strip = strip

    b = 60 / bpm # amount of time between led peaks (sec)

    c = 255 * ((b/lifetime) - 1) # idek

    for i in range(len(new_strip)):
        new_strip[i][3] = ((-(time.time() - i * lifetime / length) % b) / b * (255 + c)) - c
        if new_strip[i][3] < 0:
            new_strip[i][3] = 0

    return new_strip


# rain


# bounce


# strobe
def strobe(strip, bpm=default_bpm * 10, offset=0):
    new_strip = strip

    if (time.time() + offset/100) % (60.0/bpm) < (30.0/bpm):
        for led in new_strip:
            led[3] = 255
    else:
        for led in new_strip:
            led[3] = 0
    
    return new_strip

# ------ FOR POLY FUNCTIONS --------

# fade in out
def fadeInOut(strip, bpm=default_bpm, offset=0):
    new_strip = strip
    for led in new_strip:
        led[3] = (math.sin(2 * math.pi * (time.time() / 60) * bpm + offset) + 1)/2 * 255
    return new_strip


def swipe(strip, bpm=default_bpm, rank=0, total=3):
    new_strip = strip

    cycleTime = 60 * 2/(bpm)

    x = time.time() % cycleTime

    for led in new_strip:
        if x < (rank + 1) * cycleTime / total and x > rank * cycleTime / total:
            led[3] = 255
        else:
            led[3] = 0
        
    return new_strip


