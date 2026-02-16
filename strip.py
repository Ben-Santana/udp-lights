from fx.mono.effects import *
from fx.mono.colors import *
from functools import partial

class Strip:
    def __init__(self, length, colorFunc = idleColor, effectFunc = chase):
        self.strip = [[255, 255, 255, 255] for i in range(length)]
        self.effectFunc = effectFunc
        self.colorFunc = colorFunc
        self.color_args = []
        self.effect_args = []
        
    def _applyEffect(self):
        self.strip = self.effectFunc(self.strip, *self.effect_args)

    def _applyColor(self):
        self.strip = self.colorFunc(self.strip, *self.color_args)

    def update(self):
        self._applyColor()
        self._applyEffect()

    def rgb(self):   
        tempStrip = [[0,0,0] for i in range(len(self.strip))]
        for i in range(len(tempStrip)):
            for j in range(3):
                tempStrip[i][j] = int(self.strip[i][j] * self.strip[i][3] / 255)

        return tempStrip

