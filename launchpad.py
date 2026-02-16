import mido
import time
import json

class Launchpad:

    def __init__(self):
        self.grid = [[[3, False, None, None, None] for _ in range(9)] for _ in range(9)]

        self.inport = None
        self.outport = None

        for midi in mido.get_input_names():
            if 'Launchpad' in midi:
                self.inport = mido.open_input(midi)
                self.outport = mido.open_output(midi)

        if self.inport is None:
            raise IOError('No launchpad detected')

    def get_midi(self):
            inputs = []
            for msg in self.inport.iter_pending():
                if hasattr(msg, "note"):
                    inputs.append({"button": [int((msg.note - 10) / 10), (msg.note % 10) - 1], "on": msg.velocity==127})
            return inputs

    def msg_to_grid(self, msg):
        return lp.grid[msg["button"][0]][msg["button"][1]]

    def update(self):
        for i in range(9):
            for j in range(9):
                if self.grid[i][j][1]:
                    self._set_color([i, j], self.grid[i][j][0])
                else:
                    self._set_color([i, j], 0)

    def _grid_to_note(self, button):
        return ((button[0] + 1) * 10) + button[1] + 1

    def _set_color(self, button, color):
        msg = mido.Message('note_on', note=self._grid_to_note(button), velocity=color)
        self.outport.send(msg)
    
    def close_ports(self):
        self.inport.close()
        self.outport.close()

    def load_grid_from_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.grid = data
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except json.JSONDecodeError:
            print(f"Invalid JSON data in file: {file_path}")
    
    def save_grid_to_file(self, file_path):
        try:
            with open(file_path, 'w') as file:
                json.dump(self.grid, file, indent=4)
        except IOError:
            print(f"Error writing to file: {file_path}")




if __name__ == "__main__":
    lp = Launchpad()

    while True:
        for msg in lp.get_midi():
            if msg["on"]:
                if lp.msg_to_grid(msg)[1]:
                    lp.msg_to_grid(msg)[1] = False
                else:
                    lp.msg_to_grid(msg)[1] = True
                
        lp.update_button_colors()
        time.sleep(0.08)

    lp.close_ports()
        
