from lights import *

from fx.mono.effects import *
from fx.mono.colors import *

from fx.poly.effects import *

from network import *
import time

VIS = False
SEND = True

def main():
    lit = Lights(num_strips=3)

    lit.setStrip(0, rainbow, [], chase, [60, 10, 0.3])
    lit.setStrip(1, solid, [255, 0, 15], chase, [60, 20, 0.2])
    lit.setStrip(2, rainbow, [], chase, [60, 10, 0.3])

    # for i in range(lit.num_strips):
    #     lit.strips[i].colorFunc = rainbow
    
    # polySwipe(lit)
        
    

    if VIS:
        from stripvis import StripVisualizer
        svs = StripVisualizer(30, 600, lit)

    while True:
        lit.update()
        if VIS:
            svs.update()
        if SEND:
            updateLights(stripToBytes(lit.rgb()))
        time.sleep(0.01)



if __name__ == "__main__":
    main()
