from strip import Strip

class Lights:
    def __init__(self, strip_length=80, num_strips=6, wled_addr = {"192.168.0.101": [0, 1, 2], "192.168.0.100": [3, 4, 5]}, port=21324):
        self.num_strips = num_strips
        self.strip_length = strip_length
        self.strips = [Strip(strip_length) for _ in range(num_strips)]
        self.wled_addr = wled_addr
        self.port = port
    
    # update strips
    def update(self):
        for strip in self.strips:
            strip.update()
        
    def setStrip(self, 
                index=0, 
                effectFunc=None, 
                effect_args=None,
                colorFunc=None, 
                color_args=None):
        if effectFunc is not None:
            self.strips[index].effectFunc = effectFunc
        if effect_args is not None:
            self.strips[index].effect_args = effect_args
        if colorFunc is not None:
            self.strips[index].colorFunc = colorFunc
        if color_args is not None:
            self.strips[index].color_args = color_args
