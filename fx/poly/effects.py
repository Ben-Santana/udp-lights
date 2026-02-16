# Defines cross strip effect functions Lights -> Lights
from fx.mono.effects import *
import time

def polySinWave(lit, bpm, offset=0.5):
    for i in range(lit.num_strips):
        lit.setStrip(i, fadeInOut, [bpm/2, i * offset])

def polySwipe(lit, bpm):
    for i in range(lit.num_strips):
        lit.setStrip(i, swipe, [bpm*4, i, lit.num_strips])

def polySwipeBack(lit, bpm):
    for i in range(lit.num_strips):
        lit.setStrip(lit.num_strips - i - 1, swipe, [bpm*4, i, lit.num_strips])