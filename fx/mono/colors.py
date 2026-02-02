# Defines color functions for single strip strip[] -> strip[] modifies rgb values
import colorsys
import time

def idleColor(strip):
    return strip

def solid(strip, r, g, b):
    new_strip = strip
    
    for led in new_strip:
        led[0] = r
        led[1] = g
        led[2] = b

    return new_strip

def rainbow(strip):

    new_strip = strip
    h = time.time() / 10 % 1
    r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)

    for led in new_strip:
        led[0] = int(r * 255)
        led[1] = int(g * 255)
        led[2] = int(b * 255)

    return new_strip
    
