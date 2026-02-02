from strip import Strip

class Lights:
    def __init__(self, strip_length=70, num_strips=3, ip_addr="127.0.0.1", port=21324):
        self.num_strips = num_strips
        self.strip_length = strip_length
        self.strips = [Strip(strip_length) for _ in range(num_strips)]
        self.ip_addr = ip_addr
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
        if effectFunc:
            self.strips[index].effectFunc = effectFunc
        if effect_args:
            self.strips[index].effect_args = effect_args
        if colorFunc:
            self.strips[index].colorFunc = colorFunc
        if color_args:
            self.strips[index].color_args = color_args


    # returns [..., [r, g, b], ...]
    def rgb(self):
        temp = []
        for s in range(self.num_strips):
            temp += self.strips[s].rgb()
        return temp
