from lights import *
from fx.mono.effects import *
from fx.mono.colors import *
from fx.poly.effects import *
from fx.poly.colors import *
from network import *
import time
from config.main import *

next_frame = time.perf_counter()

VIS = True
SEND = True

def main():
    lit = Lights(num_strips=3)

    lit.setStrip(0, rainbow, [], chase, [60, 10, 0.3])
    lit.setStrip(1, rainbow, [], chase, [60, 20, 0.2])
    lit.setStrip(2, rainbow, [], chase, [60, 10, 0.3])
    
    # polySwipe(lit) 

    if VIS:
        from stripvis import StripVisualizer
        svs = StripVisualizer(30, 600, lit)

    while True:
        now = time.perf_counter()

        if now >= next_frame:
            lit.update()
            if VIS:
                svs.update()
            if SEND:
                updateLights(stripToBytes(lit.rgb()))
        else:
            time.sleep(0.0001)



if __name__ == "__main__":
    main()
