import customtkinter as ctk
import os
import json

class LaunchpadGUI(ctk.CTk):
    def __init__(self, lp_instance):
        super().__init__()
        self.lp = lp_instance
        self.current_file_path = None
        self.selected_coords = (0, 0)
        self.temp_selected_color = 0
        
        # Window Configuration
        self.title("Launchpad MK2 - Pro Editor")
        self.grid_size = 540
        self.side_panel_width = 220

        self.bind("<Return>", lambda event: self.save_current_button())
        
        total_width = self.side_panel_width + self.grid_size + self.side_panel_width
        self.geometry(f"{total_width}x{self.grid_size}")
        self.resizable(False, False)
        self.configure(fg_color="black")

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

        # Main Grid Config
        self.grid_columnconfigure(0, weight=0, minsize=self.side_panel_width)
        self.grid_columnconfigure(1, weight=0, minsize=self.grid_size)
        self.grid_columnconfigure(2, weight=0, minsize=self.side_panel_width)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Panel (Loader / Creator)
        self.left_panel = ctk.CTkFrame(self, width=self.side_panel_width, corner_radius=0, fg_color="#1e1e1e", border_width=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.grid_propagate(False)
        self._setup_config_ui()

        # 2. Center Panel (Grid)
        self.launchpad_frame = ctk.CTkFrame(self, width=self.grid_size, height=self.grid_size, fg_color="black", corner_radius=0)
        self.launchpad_frame.grid(row=0, column=1, sticky="nsew")
        
        # 3. Right Panel (Scrollable Editor)
        # Note: 'height' must be set or 'sticky="nsew"' must be used for scroll to trigger
        self.right_panel = ctk.CTkScrollableFrame(
            self, 
            width=self.side_panel_width - 15, # Space for scrollbar
            corner_radius=0, 
            fg_color="#1e1e1e",
            scrollbar_button_color="#333333",
            scrollbar_button_hover_color="#444444",
            border_width=0
        )
        self.right_panel.grid(row=0, column=2, sticky="nsew")
        self._setup_editor_ui()

        self.buttons = [[None for _ in range(9)] for _ in range(9)]
        self._build_grid()

    def _get_config_names(self):
        config_dir = 'button_configs'
        if not os.path.exists(config_dir): os.makedirs(config_dir)
        return [f[:-5] for f in os.listdir(config_dir) if f.endswith('.json')]

    def _setup_config_ui(self):
        inner_width = self.side_panel_width - 40 
        
        # --- LOAD SECTION ---
        ctk.CTkLabel(self.left_panel, text="Load Config", font=("Arial", 16, "bold")).pack(pady=(30, 10))
        self.config_combobox = ctk.CTkComboBox(self.left_panel, values=self._get_config_names(), width=inner_width)
        self.config_combobox.pack(pady=5)
        ctk.CTkButton(self.left_panel, text="Load Selected", command=self.load_selected_file, width=inner_width).pack(pady=5)
        
        # --- CREATE SECTION (Replacing the Pop-up Dialog) ---
        ctk.CTkLabel(self.left_panel, text="Create New", font=("Arial", 16, "bold")).pack(pady=(40, 10))
        self.new_name_entry = ctk.CTkEntry(self.left_panel, placeholder_text="Enter name...", width=inner_width)
        self.new_name_entry.pack(pady=5)
        ctk.CTkButton(self.left_panel, text="Create & Load", command=self.create_new_config, 
                      fg_color="#2d5a27", hover_color="#3a7432", width=inner_width).pack(pady=5)
        
        self.status_label = ctk.CTkLabel(self.left_panel, text="No file loaded", text_color="gray")
        self.status_label.pack(side="bottom", pady=30)

    def create_new_config(self):
        name = self.new_name_entry.get().strip()
        if not name:
            self.status_label.configure(text="Error: Name empty", text_color="#FF4444")
            return
            
        filename = f"{name}.json"
        filepath = os.path.join('button_configs', filename)
        
        if os.path.exists(filepath):
            self.status_label.configure(text="Error: Exists", text_color="#FF4444")
            return

        # Default: color 0, on (True), strings null
        default_grid = [[[0, True, None, None, None] for _ in range(9)] for _ in range(9)]
        
        try:
            with open(filepath, 'w') as f:
                json.dump(default_grid, f, indent=4) #
            
            # Reset entry and refresh list
            self.new_name_entry.delete(0, 'end')
            names = self._get_config_names()
            self.config_combobox.configure(values=names)
            self.config_combobox.set(name)
            self.load_selected_file()
        except Exception as e:
            print(f"Error: {e}")

    def load_selected_file(self):
        selected = self.config_combobox.get()
        if selected:
            self.current_file_path = os.path.join('button_configs', f"{selected}.json") #
            self.lp.load_grid_from_file(self.current_file_path) #
            self.status_label.configure(text=f"Loaded: {selected}", text_color="#00FF00")

    def _setup_editor_ui(self):
        """Elements inside the right_panel ScrollableFrame"""
        inner_width = self.side_panel_width - 60
        
        self.edit_label = ctk.CTkLabel(self.right_panel, text="Button Settings", font=("Arial", 16, "bold"))
        self.edit_label.pack(pady=(15, 10))

        # Palette
        self.palette_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.palette_container.pack(pady=5)

        self.selected_color_preview = ctk.CTkLabel(self.right_panel, text="Selected: Code 0")
        self.selected_color_preview.pack(pady=5)
        
        self.palette_buttons = {}
        for i in range(64):
            r, c = divmod(i, 8)
            p_btn = ctk.CTkButton(
                self.palette_container, text="", width=20, height=20,
                fg_color=self.color_palette[i], corner_radius=2,
                border_width=0, command=lambda val=i: self._set_temp_color(val)
            )
            p_btn.grid(row=r, column=c, padx=1, pady=1)
            self.palette_buttons[i] = p_btn

        self.on_var = ctk.BooleanVar()
        self.on_check = ctk.CTkCheckBox(self.right_panel, text="LED Active", variable=self.on_var)
        self.on_check.pack(pady=15)

        self.str_entries = []
        labels = ["HTTP", "UDP", "Misc. Function"]
        for label in labels:
            ctk.CTkLabel(self.right_panel, text=f"{label}:").pack()
            entry = ctk.CTkEntry(self.right_panel, width=inner_width)
            entry.pack(pady=5)
            self.str_entries.append(entry)

        self.save_btn = ctk.CTkButton(self.right_panel, text="Save Button", state="disabled", 
                                      command=self.save_current_button, width=inner_width)
        self.save_btn.pack(pady=(20, 40))

    def _set_temp_color(self, color_code):
        self.temp_selected_color = color_code
        self.selected_color_preview.configure(text=f"Selected: Code {color_code}", text_color=self.color_palette[color_code])
        for code, btn in self.palette_buttons.items():
            btn.configure(border_width=1 if code == color_code else 0, border_color="white")

    def _build_grid(self):
        btn_size = self.grid_size // 9
        for r in range(9):
            for c in range(9):
                btn = ctk.CTkButton(
                    self.launchpad_frame, text="", width=btn_size, height=btn_size,
                    corner_radius=0, border_width=1, border_color="#1a1a1a",
                    fg_color=self.color_palette[0], hover_color="#333333",
                    command=lambda row=r, col=c: self._select_button(row, col)
                )
                btn.place(x=c * btn_size, y=(8 - r) * btn_size)
                self.buttons[r][c] = btn

    def _select_button(self, row, col):
        self.selected_coords = (row, col)
        data = self.lp.grid[row][col] #
        self.edit_label.configure(text=f"Button: {row}, {col}")
        self.save_btn.configure(state="normal")
        self._set_temp_color(data[0]) #
        self.on_var.set(data[1]) #
        for i, entry in enumerate(self.str_entries):
            entry.delete(0, 'end')
            val = data[i+2] if data[i+2] is not None else "" #
            entry.insert(0, val)

    def save_current_button(self):
        row, col = self.selected_coords
        new_on = self.on_var.get()
        strings = [e.get() if e.get().strip() != "" else None for e in self.str_entries]
        new_data = [self.temp_selected_color, new_on] + strings
        self.lp.grid[row][col] = new_data #
        if self.current_file_path:
            self.lp.save_grid_to_file(self.current_file_path) #

    def sync(self):
        for r in range(9):
            for c in range(9):
                # Data structure: [color, is_on, str, str, str]
                color_code, is_on, _, __, ___ = self.lp.grid[r][c] #
                target_hex = self.color_palette.get(color_code, "#FFFFFF") if is_on else self.color_palette[0]
                if self.buttons[r][c].cget("fg_color") != target_hex:
                    self.buttons[r][c].configure(fg_color=target_hex)
        self.update_idletasks()
        self.update()