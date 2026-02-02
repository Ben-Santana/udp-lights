from lights import *
from fx.mono.effects import *
from fx.mono.colors import *
from fx.poly.effects import *
from fx.poly.colors import *
from network import *
import time
from config.main import *

VIS = True
SEND = True


def main():
    lit = Lights(num_strips=3)

    lit.setStrip(0, sinWave, [], rainbow, [])
    lit.setStrip(1, chase, [60, 10, 0.2], rainbow, [])
    lit.setStrip(2, sinWave, [], rainbow, [])

    # lit.setStrip(0, rainbow, [], strobe, [60 * 10, 10])
    # lit.setStrip(1, rainbow, [], strobe, [60 * 10, 50])
    # lit.setStrip(2, rainbow, [], strobe, [60 * 10, 80])

    # lit.setStrip(0, colorFunc=rainbow)
    # lit.setStrip(1, colorFunc=rainbow)
    # lit.setStrip(2, colorFunc=rainbow)
    # polySinWave(lit)

    next_frame_time = time.perf_counter()

    # init pygame screen if vis is on
    if VIS:
        from stripvis import StripVisualizer
        svs = StripVisualizer(30, 600, lit)

    next_frame_time = time.perf_counter()

    while True:
        current_time = time.perf_counter()
        if current_time >= next_frame_time:
            lit.update()
            if VIS:
                svs.update()
            if SEND:
                updateLights(stripToBytes(lit.rgb()))
            next_frame_time += frame_duration


if __name__ == "__main__":
    main()
