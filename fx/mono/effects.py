# Defines effect functions strip[] -> strip[] modifies alpha values
import time
import math
from config.effects import *
import random

# idle
def idleEffect(strip):
    return strip

# sin
def sinWave(strip, bpm=default_bpm, wave_length=5):
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
def rain(strip, bpm=default_bpm * 3, drop_length=20, density=0.5):
    new_strip = strip
    n = len(new_strip)
    
    t = time.time() * (bpm / 60)
    
    for i in range(n):
        lane_seed = math.sin(i * 0.5) * 1000 * random.random()
        drop_val = (t + lane_seed) % 10.0 
        
        if drop_val < 1.0:
            brightness = (1.0 - drop_val) * 255
        
            if (math.sin(i + (t // 10)) > (1 - density)):
                new_strip[i][3] = brightness
            else:
                new_strip[i][3] = 0
        else:
            new_strip[i][3] = 0
            
    return new_strip

# bounce
def bounce(strip, bpm=default_bpm, width=4):
    new_strip = strip
    n = len(new_strip)
    
    t = time.time() * (bpm / 60)
    triangle_wave = 1 - abs((2 * t) % 2 - 1)
    center = triangle_wave * (n - 1)
    
    for i in range(n):
        dist = abs(i - center)
        if dist < width:
            new_strip[i][3] = (1 - (dist / width)) * 255
        else:
            new_strip[i][3] = 0
            
    return new_strip

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

# pulse
def pulse(strip, start_time, speed=5, bpm=default_bpm):
    new_strip = strip
    
    alpha = 1 / (((time.time() - start_time) * speed) + 0.8)

    for led in new_strip:
        led[3] = min(255, int(alpha * 255))

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

def radialPulse(strip, bpm=default_bpm, strip_idx=0, center_x=0, center_y=0, width=5):
    new_strip = strip
    t = (time.time() * (bpm / 60)) % 15 # The "radius" of the ripple expanding
    
    for led_idx in range(len(new_strip)):
        # 2D distance calculation: x = strip_idx, y = led_idx
        dx = strip_idx - center_x
        dy = led_idx - center_y
        dist = math.sqrt(dx**2 + dy**2)
        
        # Check if this LED is on the "edge" of the expanding ripple
        diff = abs(dist - t * 5) # Multiply t by speed factor
        
        if diff < width:
            # Fade based on distance from the ripple's edge
            new_strip[led_idx][3] = (1 - (diff / width)) * 255
        else:
            new_strip[led_idx][3] = 0
            
    return new_strip

def diamondPulse(strip, bpm=default_bpm, strip_idx=0, center_x=0, center_y=0, width=4):
    new_strip = strip
    # t is our expanding radius
    t = (time.time() * (bpm / 60) * 8) % 60 
    
    for led_idx in range(len(new_strip)):
        # Manhattan Distance: sum of absolute differences
        dist = abs(strip_idx - center_x) + abs(led_idx - center_y)
        
        # Check proximity to the ripple edge
        diff = abs(dist - t)
        
        if diff < width:
            # Linear fade for the diamond's edge
            new_strip[led_idx][3] = (1 - (diff / width)) * 255
        else:
            new_strip[led_idx][3] = 0
            
    return new_strip


