import customtkinter as ctk
import time
from launchpad import Launchpad # Ensure this matches your filename

class LaunchpadGUI(ctk.CTk):
    def __init__(self, lp_instance):
        super().__init__()
        self.lp = lp_instance
        
        # Window Configuration
        self.title("Launchpad MK2")
        self.window_size = 540  # 540 is divisible by 9 (60px per button)
        self.geometry(f"{self.window_size}x{self.window_size}")
        self.resizable(False, False)
        self.configure(fg_color="black")
        
        # Note for Hyprland: You may need to add this to your hyprland.conf:
        # windowrule = float, ^(Launchpad MK2)$
        # windowrule = size 540 540, ^(Launchpad MK2)$

        self.color_palette = {
            0: "#242424", 1: "#7e7e7e", 2: "#b2b2b2", 3: "#ffffff",
            4: "#ff7e7e", 5: "#ff0000", 6: "#7e0000", 7: "#7e3b3b",
            8: "#ffdebd", 9: "#ff8400", 10: "#7e4200", 11: "#7e5a3b",
            12: "#ffff7e", 13: "#ffff00", 14: "#7e7e00", 15: "#7e7e3b",
            16: "#bdff7e", 17: "#84ff00", 18: "#427e00", 19: "#5a7e3b",
            20: "#7eff7e", 21: "#00ff00", 22: "#007e00", 23: "#3b7e3b",
            24: "#7effbd", 25: "#00ff84", 26: "#007e42", 27: "#3b7e5a",
            28: "#7effff", 29: "#00ffff", 30: "#007e7e", 31: "#3b7e7e",
            32: "#7ebdff", 33: "#0084ff", 34: "#00427e", 35: "#3b5a7e",
            36: "#7e7eff", 37: "#0000ff", 38: "#00007e", 39: "#3b3b7e",
            40: "#bd7eff", 41: "#8400ff", 42: "#42007e", 43: "#5a3b7e",
            44: "#ff7eff", 45: "#ff00ff", 46: "#7e007e", 47: "#7e3b7e",
            48: "#ff7ebd", 49: "#ff0084", 50: "#7e0042", 51: "#7e3b5a",
            52: "#ffbd7e", 53: "#ff5a00", 54: "#7e3b00", 55: "#7e5a3b",
            56: "#ffbdff", 57: "#ff00ff", 58: "#7e007e", 59: "#7e3b7e",
            60: "#ff7e42", 61: "#bd9e3b", 62: "#9e7e3b", 63: "#7e7e3b",
        }

        self.buttons = [[None for _ in range(9)] for _ in range(9)]
        self._build_grid()

    def _build_grid(self):
        """Builds a zero-margin grid by manually calculating pixel sizes."""
        btn_size = self.window_size // 9
        
        for r in range(9):
            for c in range(9):
                # We use a standard tkinter Button wrapper or CTkButton 
                # but force internal padding to 0.
                btn = ctk.CTkButton(
                    self,
                    text="",
                    width=btn_size,
                    height=btn_size,
                    corner_radius=0,
                    border_width=0,   # Set to 0 to remove internal margins
                    border_spacing=0, # Crucial for removing CTk internal padding
                    fg_color=self.color_palette[0],
                    hover=False,
                    command=lambda row=r, col=c: self._press(row, col)
                )
                # Position 0,0 at bottom-left
                # Grid can sometimes add 1px gaps; place is absolute pixel control
                btn.place(x=c * btn_size, y=(8 - r) * btn_size)
                self.buttons[r][c] = btn

    def _press(self, r, c):
        self.lp.grid[r][c][1] = not self.lp.grid[r][c][1]

    def sync(self):
        """Sync visuals and handle window events."""
        for r in range(9):
            for c in range(9):
                color_code, is_on = self.lp.grid[r][c]
                target_hex = self.color_palette.get(color_code, "#FFFFFF") if is_on else self.color_palette[0]
                
                if self.buttons[r][c].cget("fg_color") != target_hex:
                    self.buttons[r][c].configure(fg_color=target_hex)
        
        self.update_idletasks()
        self.update()

if __name__ == "__main__":
    lp = Launchpad()
    app = LaunchpadGUI(lp)

    try:
        while True:
            for msg in lp.get_midi():
                r, c = msg["button"]
                if 0 <= r < 9 and 0 <= c < 9:
                    if msg["on"]:
                        lp.grid[r][c][1] = not lp.grid[r][c][1]

            lp.update_button_colors()
            app.sync()
            time.sleep(0.01)
    except (ctk.TclError, KeyboardInterrupt):
        lp.close_ports()