# Defines cross strip effect functions Lights -> Lights
from fx.mono.effects import *
from config.effects import default_bpm
import time

def polySinWave(lit, offset=0.5):
    for i in range(lit.num_strips):
        lit.setStrip(i, fadeInOut, [default_bpm/2, i * offset])

def polySwipe(lit):
    for i in range(lit.num_strips):
        lit.setStrip(i, swipe, [default_bpm*4, i, lit.num_strips])

def polyRipple(lit, speed=1.5):
    center = (lit.num_strips - 1) / 2
    t = time.time() * speed
    
    for i in range(lit.num_strips):
        dist_from_center = abs(i - center)
        offset = dist_from_center * 0.2 
        lit.setStrip(i, fadeInOut, [default_bpm, offset])

def polyOmniRipple(lit, center_strip=None, center_led=None):
    # Default to the dead center of your entire setup
    if center_strip is None: center_strip = lit.num_strips / 2
    if center_led is None: center_led = lit.strip_length / 2 # Adjust based on your strip length
    
    for i in range(lit.num_strips):
        # Pass the strip's own index and the global center point
        lit.setStrip(i, radialPulse, [default_bpm, i, center_strip, center_led])

def polyDiamondRipple(lit, cx=None, cy=None):
    if cx is None: cx = lit.num_strips // 2
    if cy is None: cy = lit.strip_length // 2
    for i in range(lit.num_strips):
        lit.setStrip(i, diamondPulse, [default_bpm, i, cx, cy])