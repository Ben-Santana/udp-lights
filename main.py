import time
from launchpad import Launchpad
from launchpad_gui import LaunchpadGUI
from lights import Lights

# might not be needed
from fx.mono.effects import *
from fx.mono.colors import *
from fx.poly.effects import *
from fx.poly.colors import *
from network import *

import ast

VIS = False
SEND = True

fps = 60.0
frame_duration = 1.0 / fps

def handle_http(input_str):
    """Placeholder for HTTP logic."""
    print(f"Executing HTTP Request to: {data}")

# [[setStrip inputs], ..., [setStrip inputs]]
def handle_udp(input_string, lights):
    """Placeholder for UDP logic."""

    data = eval(input_string)

    # Check if the result is a list
    if not isinstance(data, list):
        raise ValueError("Input is not a list structure.")

    # Check if it is 2D (all elements are lists)
    if not all(isinstance(item, list) for item in data):
        raise ValueError("Input is a 1D list, but a 2D list is required.")

    for command in data:
        index, ef, ea, cf, ca = command
        lights.setStrip(index, ef, ea, cf, ca)

def main():
    # Initialize the hardware and the GUI
    lp = Launchpad()
    gui = LaunchpadGUI(lp)
    lights = Lights()

    for i in range(3):
        lights.setStrip(i, chase, [], rainbow, [])
    
    print("Main loop started. Press Ctrl+C to exit.")

    next_frame_time = time.perf_counter()

    if VIS:
        from stripvis import StripVisualizer
        svs = StripVisualizer(30, 600, lights)
    
    try:
        while True:
            current_time = time.perf_counter()
            # 1. Get MIDI inputs: returns [button_coords, on_bool]
            # Coordinates are [row, col]
            midi_data = lp.get_midi()
            
            for msg in midi_data:
                row, col = msg["button"]
                is_pressed = msg["on"]
                
                # We only trigger logic when the button is pressed (True)
                if is_pressed:
                    # Retrieve the configuration for this specific button
                    # Format: [color, is_on, action_str, id_str, tag_str]
                    btn_config = lp.grid[row][col]
                    color, active, http_val, udp_val, tag_val = btn_config
                    
                    # Check if the button is enabled in the database
                    if active:
                        # Logic: Check HTTP first, then UDP
                        if http_val is not None:
                            handle_http(http_val)
                        
                        if udp_val is not None:
                            handle_udp(udp_val, lights)
                        
                        # Note: the last value is currently ignored per requirements.

            # 2. Update the hardware Launchpad LEDs
            lp.update()
            
            # 3. Update the GUI visuals and handle window events
            gui.sync()

            # Update lights
            if current_time >= next_frame_time:
                lights.update()
                if VIS:
                    svs.update()
                if SEND:
                    updateLights(lights, stripToBytes(lights.rgb()))
                next_frame_time += frame_duration
            
            # Small sleep to prevent high CPU usage
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        lp.close_ports()
        gui.destroy()

if __name__ == "__main__":
    main()