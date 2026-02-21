import ast
import time
from launchpad import Launchpad
from launchpad_gui import LaunchpadGUI
from lights import Lights
import mido
import asyncio

from fx.mono.effects import *
from fx.mono.colors import *
from fx.poly.effects import *
from fx.poly.colors import *
from network import *

# +=======+ Config +=======+ #

VIS = False # display pygame visualizer of lights
SEND = True # send udp / http packets to WLED servers
num_strips = 6 # total number of led strips
fps = 60.0
bpm = 120
# wled_addr = {"192.168.0.101": [0, 1, 2], "192.168.0.100": [3, 4, 5]} # mapping strips to wled servers (0 indexed)
wled_addr = {"192.168.0.100": [3, 4, 5]}

# +========================+ #

frame_duration = 1.0 / fps


def handle_http(input_str):
    for ip in wled_addr.keys():
        asyncio.run(triggerLED(input_str, ip))
        # TODO: handle http requests (take a look it you can set the lights to follow WLED presets through UDP messaages)

# [[setStrip inputs], ..., [setStrip inputs]]
def handle_udp(input_string, lights):
    """Placeholder for UDP logic."""

    data = eval(input_string)

    # check if the result is a list
    if not isinstance(data, list):
        raise ValueError("Input is not a list structure.")

    # check if it is 2D (all elements are lists)
    if not all(isinstance(item, list) for item in data):
        raise ValueError("Input is a 1D list, but a 2D list is required.")

    for command in data:
        index, ef, ea, cf, ca = command[0:5]
        misc = command[5] if len(command) > 5 else None
        if type(ef) is type(""):
            ef = eval(ef)
        if type(cf) is type(""):
            cf = eval(cf)
        lights.setStrip(index, ef, ea, cf, ca)
        if misc is not None:
            eval(misc)

def add_to_bpm(amount):
    global bpm
    bpm += amount

def main():
    lp = None
    try:
        for mid in mido.get_input_names():
            if "Launch" in mid:
                lp = Launchpad()
    except (IOError, OSError, Exception):
        pass
        
    if lp is None:
        print("Launchpad not connected — GUI config editor only.")

    gui = LaunchpadGUI(lp, num_strips=num_strips)

    lights = Lights(num_strips=num_strips, wled_addr=wled_addr)

    # default start effect for lights
    for i in range(num_strips):
        lights.setStrip(i, idleEffect, [], None, None)
    
    print("Main loop started. Press Ctrl+C to exit.")

    next_frame_time = time.perf_counter()

    if VIS:
        from stripvis import StripVisualizer
        svs = StripVisualizer(30, 600, lights)

    # +=====+ Main Loop +=====+ #
    try:
        while True:
            # time for frame rate management
            current_time = time.perf_counter()

            # handle launchpad if its connected
            if lp is not None:
                # get midi inputs from launchpad
                midi_data = lp.get_midi()
                
                # loop through and process midi input messages
                for msg in midi_data:
                    row, col = msg["button"]
                    is_pressed = msg["on"]
                    
                    if is_pressed:
                        btn_config = lp.grid[row][col]
                        color, active, http_val, udp_val, func = btn_config
                    
                        if active:
                            if http_val is not None:
                                handle_http(http_val)
                            
                            if udp_val is not None:
                                handle_udp(udp_val, lights)
                            
                            if func is not None:
                                eval(func)

            # update the launchpad and gui
            if lp is not None: lp.update()
            gui.sync(bpm=bpm)

            # update lights
            if current_time >= next_frame_time:
                lights.update()
                if VIS:
                    svs.update()
                if SEND:
                    for ip, strips in lights.wled_addr.items():
                        sendUDP(ip, lights.port, lightToBytes(lights, strips))
                next_frame_time += frame_duration
            
            # Small sleep to prevent high CPU usage
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if lp is not None: lp.close_ports()
        gui.destroy()

if __name__ == "__main__":
    main()