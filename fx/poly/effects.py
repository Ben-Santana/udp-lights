# Defines cross strip effect functions Lights -> Lights
from fx.mono.effects import *

def polySinWave(lit, offset=1):
    for i in range(lit.num_strips):
        lit.setStrip(i, fadeInOut, [default_bpm/2, i * offset])

def polySwipe(lit):
    for i in range(lit.num_strips):
        lit.setStrip(i, swipe, [default_bpm*4, i, lit.num_strips])