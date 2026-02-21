import customtkinter as ctk
import os
import json
import ast

# Optional: load effect/color metadata for forms (skip if fx not available)
try:
    from fx_meta import get_color_meta, get_effect_meta
    _color_meta = get_color_meta()
    _effect_meta = get_effect_meta()
except Exception:
    _color_meta = {}
    _effect_meta = {}


def _parse_param_value(s):
    """Parse a param string: int, float, or leave as identifier (e.g. bpm)."""
    s = (s or "").strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _args_to_udp_part(vals):
    """Build UDP-safe string for args list. None or all blank -> None."""
    if vals is None:
        return "None"
    filled = []
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        filled.append(v)
    if not filled:
        return "None"
    # Build list string for eval: numbers as literals, identifiers/expressions unquoted
    parts = []
    for v in filled:
        if isinstance(v, (int, float)):
            parts.append(repr(v))
        else:
            parts.append(str(v))
    return "[" + ", ".join(parts) + "]"


def _split_by_comma_at_depth(s):
    """Split string by commas at depth 0 (depth counted by [ and ] and ( and ))."""
    s = (s or "").strip()
    if not s:
        return []
    depth = 0
    start = 0
    parts = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in "[(":
            depth += 1
        elif c in "])":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append(s[start:i].strip())
            start = i + 1
        i += 1
    if start < len(s):
        parts.append(s[start:].strip())
    return parts


def _split_list_elements(list_str):
    """Given a string like '[time.time(), 10]' or 'None', return list of param source strings or None."""
    list_str = (list_str or "").strip()
    if not list_str or list_str == "None":
        return None
    if list_str[0] != "[":
        return None
    inner = list_str[1:-1].strip()
    if not inner:
        return []
    return _split_by_comma_at_depth(inner)


def _safe_udp_namespace():
    """Namespace for eval'ing UDP config strings: None + effect/color names as strings + bpm + time module."""
    ns = {"None": None, "null": None}
    for name in _effect_meta:
        ns[name] = name
    for name in _color_meta:
        ns[name] = name
    ns["bpm"] = "bpm"
    ns["time"] = __import__("time")  # so time.time() in effect args (e.g. pulse) evaluates
    return ns


def _parse_udp_for_strip_zero(udp_val):
    """Parse UDP string and return (effect_name, effect_args, color_name, color_args) for strip 0.
    Returns (None, None, None, None) if not parseable or no strip 0."""
    strips = _parse_udp_all_strips(udp_val)
    for idx, ef_name, ea, cf_name, ca, misc in strips:
        if idx == 0:
            return ef_name, ea, cf_name, ca
    return None, None, None, None


def _parse_udp_all_strips_raw(udp_val):
    """Parse UDP string keeping effect/color args as source strings (no eval of args). Returns same format as _parse_udp_all_strips or [] on failure."""
    if not udp_val or not isinstance(udp_val, str) or udp_val.strip() == "":
        return []
    s = udp_val.strip()
    if s[0] != "[" or len(s) < 2:
        return []
    inner = s[1:-1].strip()
    if not inner:
        return []
    cmd_strings = _split_by_comma_at_depth(inner)
    if not cmd_strings:
        return []
    ns = _safe_udp_namespace()
    out = []
    for cmd_str in cmd_strings:
        cmd_str = cmd_str.strip()
        if cmd_str[0] != "[" or len(cmd_str) < 2:
            continue
        elem_inner = cmd_str[1:-1].strip()
        elems = _split_by_comma_at_depth(elem_inner)
        if len(elems) < 5:
            continue
        try:
            idx = eval(elems[0], ns)
        except Exception:
            continue
        try:
            ef = eval(elems[1], ns)
        except Exception:
            ef = elems[1].strip() if elems[1].strip() and elems[1].strip() != "None" else None
        try:
            cf = eval(elems[3], ns)
        except Exception:
            cf = elems[3].strip() if elems[3].strip() and elems[3].strip() != "None" else None
        ef_name = getattr(ef, "__name__", None) if not isinstance(ef, str) else (ef if ef else None)
        cf_name = getattr(cf, "__name__", None) if not isinstance(cf, str) else (cf if cf else None)
        ea = _split_list_elements(elems[2])
        ca = _split_list_elements(elems[4])
        misc = None
        if len(elems) > 5:
            try:
                misc = eval(elems[5], ns)
            except Exception:
                misc = elems[5].strip() or None
        if misc is not None and isinstance(misc, str) and misc.strip() == "":
            misc = None
        out.append((idx, ef_name, ea, cf_name, ca, misc))
    return out


def _parse_udp_all_strips(udp_val):
    """Parse UDP string and return list of (index, effect_name, effect_args, color_name, color_args, misc).
    effect_args and color_args are kept as lists of source strings when possible (e.g. 'time.time()' not evaluated)."""
    if not udp_val or not isinstance(udp_val, str) or udp_val.strip() == "":
        return []
    # Prefer raw parse so param fields show source (e.g. time.time()) not evaluated values
    raw = _parse_udp_all_strips_raw(udp_val)
    if raw:
        return raw
    try:
        data = ast.literal_eval(udp_val)
    except (ValueError, SyntaxError):
        ns = _safe_udp_namespace()
        while True:
            try:
                data = eval(udp_val, ns)
                break
            except NameError as e:
                name = getattr(e, "name", None)
                if name and name not in ns:
                    ns[name] = name
                else:
                    return []
            except Exception:
                return []
    if not isinstance(data, list) or not data:
        return []
    out = []
    for cmd in data:
        if not isinstance(cmd, list) or len(cmd) < 5:
            continue
        idx, ef, ea, cf, ca = cmd[0], cmd[1], cmd[2], cmd[3], cmd[4]
        misc = cmd[5] if len(cmd) > 5 else None
        if misc is not None and isinstance(misc, str) and misc.strip() == "":
            misc = None
        ef_name = getattr(ef, "__name__", None) if not isinstance(ef, str) else (ef if ef else None)
        cf_name = getattr(cf, "__name__", None) if not isinstance(cf, str) else (cf if cf else None)
        # Convert evaluated args to strings for display (we've lost the original source)
        ea_str = [str(x) for x in ea] if ea is not None and isinstance(ea, (list, tuple)) else None
        ca_str = [str(x) for x in ca] if ca is not None and isinstance(ca, (list, tuple)) else None
        out.append((idx, ef_name, ea_str, cf_name, ca_str, misc))
    return out


def _default_grid():
    """Default 9x9 button grid when no config is loaded."""
    return [[[0, True, None, None, None] for _ in range(9)] for _ in range(9)]


class LaunchpadGUI(ctk.CTk):
    def __init__(self, lp_instance, num_strips=8):
        super().__init__()
        self.lp = lp_instance  # None when Launchpad not connected
        self.num_strips = num_strips
        self.current_file_path = None
        self.selected_coords = (0, 0)
        self.temp_selected_color = 0
        self.bpm = 120
        # GUI-owned grid: always use this for display/edit; keep in sync with lp.grid when lp is connected
        self.grid = [r[:] for r in (lp_instance.grid if lp_instance is not None else _default_grid())]
        # Per-strip data: strip_indices = [0, 1, 5], strips_data[idx] = {effect_name, effect_args, color_name, color_args, misc}
        self.strip_indices = []
        self.strips_data = {}
        self.current_strip_index = None

        # Window Configuration (larger so strip selector fits 0–5 and more room overall)
        self.title("Launchpad MK2 - Pro Editor")
        self.grid_size = 580
        self.side_panel_width = 260

        self.bind("<Return>", lambda event: self.save_current_button())

        panel_gap = 20  # space between left panel and grid, and between grid and right panel
        content_width = self.side_panel_width + panel_gap + self.grid_size + panel_gap + self.side_panel_width
        content_height = self.grid_size
        padding = 20  # from content to window edge on all sides (so 20px from button config to outer edge)
        self.geometry(f"{content_width + padding * 2}x{content_height + padding * 2}")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e1e")

        # Theme: dark button grid; light strip selector with dark text
        self.theme = {
            "button": "#2a2a2a",           # dark grid cell
            "button_hover": "#3a3a3a",
            "button_border": "#1a1a1a",
            "button_off": "#242424",        # inactive grid cell
            "strip_bg": "#e5e5e5",         # strip selector unselected (white)
            "strip_selected": "#2a2a2a",   # selected strip: dark
            "strip_selected_border": "#ffffff",
            "strip_hover": "#d0d0d0",
            "strip_add_remove": "#d0d0d0",
            "strip_add_remove_hover": "#b0b0b0",
            "palette_border": "#888888",
            "text_color": "#333333",       # dark gray text on buttons
        }

        # Inner container: fixed size so right edge is exactly 20px from window edge
        self.main_container = ctk.CTkFrame(self, fg_color="transparent", width=content_width, height=content_height)
        self.main_container.grid(row=0, column=0, padx=padding, pady=padding, sticky="nw")
        self.main_container.grid_propagate(False)

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

        # Main Grid Config (inside container)
        self.main_container.grid_columnconfigure(0, weight=0, minsize=self.side_panel_width)
        self.main_container.grid_columnconfigure(1, weight=0, minsize=self.grid_size)
        self.main_container.grid_columnconfigure(2, weight=0, minsize=self.side_panel_width)
        self.main_container.grid_rowconfigure(0, weight=1)

        # 1. Left Panel (Loader / Creator) - 20px gap to its right (before grid)
        self.left_panel = ctk.CTkFrame(self.main_container, width=self.side_panel_width, corner_radius=0, fg_color="#1e1e1e", border_width=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, panel_gap))
        self.left_panel.grid_propagate(False)
        self._setup_config_ui()

        # 2. Center Panel (Grid)
        self.launchpad_frame = ctk.CTkFrame(self.main_container, width=self.grid_size, height=self.grid_size, fg_color="#1e1e1e", corner_radius=0)
        self.launchpad_frame.grid(row=0, column=1, sticky="nsew")

        # 3. Right Panel (Editor) - 20px gap to its left (after grid)
        self.right_panel = ctk.CTkFrame(
            self.main_container,
            width=self.side_panel_width,
            corner_radius=0,
            fg_color="#1e1e1e",
            border_width=0
        )
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(panel_gap, 0))
        self.right_panel.grid_propagate(False)
        self._setup_editor_ui()

        self.buttons = [[None for _ in range(9)] for _ in range(9)]
        self._build_grid()
        # Load initial selection into the editor form so (0,0) is shown
        self._select_button(0, 0)

    def _get_config_names(self):
        config_dir = 'button_configs'
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        return [f[:-5] for f in os.listdir(config_dir) if f.endswith('.json')]

    def _setup_config_ui(self):
        inner_width = self.side_panel_width - 24
        left_pad = 6

        ctk.CTkLabel(self.left_panel, text="Load Config", font=("Arial", 12, "bold")).pack(pady=(left_pad, 2))
        self.config_combobox = ctk.CTkComboBox(self.left_panel, values=self._get_config_names(), width=inner_width, height=24)
        self.config_combobox.pack(pady=2)
        ctk.CTkButton(self.left_panel, text="Load Selected", command=self.load_selected_file, width=inner_width, height=24, fg_color=self.theme["strip_add_remove"], hover_color=self.theme["strip_add_remove_hover"], text_color=self.theme["text_color"]).pack(pady=2)

        ctk.CTkLabel(self.left_panel, text="Create New", font=("Arial", 12, "bold")).pack(pady=(left_pad + 8, 2))
        self.new_name_entry = ctk.CTkEntry(self.left_panel, placeholder_text="Name...", width=inner_width, height=24)
        self.new_name_entry.pack(pady=2)
        ctk.CTkButton(self.left_panel, text="Create & Load", command=self.create_new_config,
                      fg_color=self.theme["strip_add_remove"], hover_color=self.theme["strip_add_remove_hover"], text_color=self.theme["text_color"], width=inner_width, height=24).pack(pady=2)

        ctk.CTkLabel(self.left_panel, text="BPM", font=("Arial", 12, "bold")).pack(pady=(left_pad + 8, 2))
        self.bpm_label = ctk.CTkLabel(self.left_panel, text="120", font=("Arial", 14))
        self.bpm_label.pack(pady=2)

        self.status_label = ctk.CTkLabel(self.left_panel, text="No file loaded", text_color="gray", font=("Arial", 10))
        self.status_label.pack(side="bottom", pady=left_pad)

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

        default_grid = [[[0, True, None, None, None] for _ in range(9)] for _ in range(9)]

        try:
            with open(filepath, 'w') as f:
                json.dump(default_grid, f, indent=4)

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
            self.current_file_path = os.path.join('button_configs', f"{selected}.json")
            try:
                with open(self.current_file_path, "r") as f:
                    self.grid = json.load(f)
                if self.lp is not None:
                    self.lp.load_grid_from_file(self.current_file_path)
            except (OSError, json.JSONDecodeError) as e:
                self.status_label.configure(text=f"Error loading: {e}", text_color="#FF4444")
                return
            self.status_label.configure(text=f"Loaded: {selected}", text_color="#00FF00")
            # Refresh editor form so it shows the current cell's data from the loaded grid
            r, c = self.selected_coords
            self._select_button(r, c)

    def _refresh_color_params(self):
        """Rebuild only the param entries in color_params_container (combo unchanged)."""
        for w in self.color_params_container.winfo_children():
            w.destroy()
        self.color_param_entries.clear()
        selected = self.color_combo_var.get()
        if selected and selected != "None" and selected in _color_meta:
            for pname, default in _color_meta[selected]:
                ctk.CTkLabel(self.color_params_container, text=f"{pname}:", font=("Arial", 10)).pack(anchor="w")
                default_str = "" if default is None else str(default)
                e = ctk.CTkEntry(self.color_params_container, placeholder_text=default_str or "opt", height=20)
                e.pack(fill="x", pady=0)
                self.color_param_entries.append((pname, e))

    def _refresh_effect_params(self):
        """Rebuild only the param entries in effect_params_container (combo unchanged)."""
        for w in self.effect_params_container.winfo_children():
            w.destroy()
        self.effect_param_entries.clear()
        selected = self.effect_combo_var.get()
        if selected and selected != "None" and selected in _effect_meta:
            for pname, default in _effect_meta[selected]:
                ctk.CTkLabel(self.effect_params_container, text=f"{pname}:", font=("Arial", 10)).pack(anchor="w")
                default_str = "" if default is None else str(default)
                e = ctk.CTkEntry(self.effect_params_container, placeholder_text=default_str or "opt", height=20)
                e.pack(fill="x", pady=0)
                self.effect_param_entries.append((pname, e))

    def _on_color_combo_change(self, *_):
        self._refresh_color_params()

    def _on_effect_combo_change(self, *_):
        self._refresh_effect_params()

    def _setup_editor_ui(self):
        # Exact pixel budget: panel = 220w x 540h. No scroll.
        W = self.side_panel_width  # 260
        H = self.grid_size         # 580
        inner_w = W - 8            # 252px: right panel content (4px pad each side)
        # Tabview content area has internal padding; use smaller width so combos/entries don't clip
        TAB_CONTENT_PAD = 10       # px each side inside tab content
        tab_content_w = inner_w - 2 * TAB_CONTENT_PAD  # 232px for widgets inside Color/Effect/Misc tabs

        # Vertical allocation (H = 580px total):
        # row0: label    14px
        # row1: tabview  (flexes with weight=1 so Strips+Save stay visible)
        # row2: gap      2px
        # row3: strips   22px
        # row4: gap      2px
        # row5: save     22px
        # row6: bottom   2px
        # Fixed: 14+2+22+2+22+2 = 64. Tabview gets 580-64 = 516 minimum.
        R_LABEL, R_TABVIEW_MIN, R_GAP1, R_STRIPS, R_GAP2, R_SAVE, R_BOTTOM = 14, 508, 2, 30, 2, 22, 2

        self.right_panel.grid_columnconfigure(0, weight=1, minsize=W)
        self.right_panel.grid_rowconfigure(0, minsize=R_LABEL)
        self.right_panel.grid_rowconfigure(1, minsize=R_TABVIEW_MIN, weight=1)
        self.right_panel.grid_rowconfigure(2, minsize=R_GAP1)
        self.right_panel.grid_rowconfigure(3, minsize=R_STRIPS)
        self.right_panel.grid_rowconfigure(4, minsize=R_GAP2)
        self.right_panel.grid_rowconfigure(5, minsize=R_SAVE)
        self.right_panel.grid_rowconfigure(6, minsize=R_BOTTOM)

        self.edit_label = ctk.CTkLabel(self.right_panel, text="Button", font=("Arial", 11, "bold"), height=R_LABEL - 4)
        self.edit_label.grid(row=0, column=0, sticky="w", padx=4, pady=0)

        self.tabview = ctk.CTkTabview(
            self.right_panel, width=inner_w, height=R_TABVIEW_MIN,
            segmented_button_fg_color=self.theme["button"],
            segmented_button_selected_color="#505050",
            segmented_button_selected_hover_color="#606060",
            segmented_button_unselected_color=self.theme["button_off"],
            segmented_button_unselected_hover_color=self.theme["button"],
            text_color="#e0e0e0",
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=4, pady=0)
        self.tabview.add("Color")
        self.tabview.add("Effect")
        self.tabview.add("Misc")

        # ---- Color tab: grid layout, full width, palette centered ----
        color_tab = self.tabview.tab("Color")
        color_tab.grid_columnconfigure(0, weight=1)
        color_tab.grid_columnconfigure(1, weight=0)  # palette column
        color_tab.grid_columnconfigure(2, weight=1)
        btn_sz = 14
        palette_w = 8 * btn_sz  # 112px
        self.palette_container = ctk.CTkFrame(color_tab, fg_color="transparent", width=palette_w, height=8 * btn_sz)
        self.palette_container.grid(row=0, column=1, pady=(2, 0), sticky="n")
        self.palette_container.grid_propagate(False)
        self.palette_buttons = {}
        for i in range(64):
            r, c = divmod(i, 8)
            p_btn = ctk.CTkButton(
                self.palette_container, text="", width=btn_sz, height=btn_sz,
                fg_color=self.color_palette[i], corner_radius=0,
                border_width=0, command=lambda val=i: self._set_temp_color(val)
            )
            p_btn.grid(row=r, column=c, padx=0, pady=0)
            self.palette_buttons[i] = p_btn

        row1 = ctk.CTkFrame(color_tab, fg_color="transparent", height=30)
        row1.grid(row=1, column=0, columnspan=3, sticky="w", padx=0, pady=(0, 4))
        row1.grid_propagate(False)
        self.selected_color_preview = ctk.CTkLabel(row1, text="0", font=("Arial", 10), width=12)
        self.selected_color_preview.grid(row=0, column=0, padx=0, pady=0)
        self.on_var = ctk.BooleanVar()
        self.on_check = ctk.CTkCheckBox(row1, text="LED on", variable=self.on_var, font=("Arial", 10), width=70)
        self.on_check.grid(row=0, column=1, padx=(8, 0), pady=0)
        row1.grid_columnconfigure(0, minsize=12)
        row1.grid_columnconfigure(1, minsize=70)

        self.color_strip_label = ctk.CTkLabel(color_tab, text="Color (strip —):", font=("Arial", 10))
        self.color_strip_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=0, pady=(4, 0))
        self.color_combo_var = ctk.StringVar(value="None")
        self.color_combo = ctk.CTkComboBox(color_tab, values=["None"] + sorted(_color_meta.keys()), variable=self.color_combo_var, width=tab_content_w, height=20, command=self._on_color_combo_change)
        self.color_combo.grid(row=3, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        self.color_params_container = ctk.CTkFrame(color_tab, fg_color="transparent")
        self.color_params_container.grid(row=4, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        color_tab.grid_rowconfigure(4, weight=1)
        self.color_param_entries = []

        # ---- Effect tab ----
        effect_tab = self.tabview.tab("Effect")
        effect_tab.grid_columnconfigure(0, weight=1, minsize=tab_content_w)
        self.effect_strip_label = ctk.CTkLabel(effect_tab, text="Effect (strip —):", font=("Arial", 10))
        self.effect_strip_label.grid(row=0, column=0, sticky="w", padx=0, pady=(2, 0))
        self.effect_combo_var = ctk.StringVar(value="None")
        self.effect_combo = ctk.CTkComboBox(effect_tab, values=["None"] + sorted(_effect_meta.keys()), variable=self.effect_combo_var, width=tab_content_w, height=20, command=self._on_effect_combo_change)
        self.effect_combo.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        self.effect_params_container = ctk.CTkFrame(effect_tab, fg_color="transparent")
        self.effect_params_container.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        effect_tab.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(effect_tab, text="HTTP:", font=("Arial", 10)).grid(row=3, column=0, sticky="w", padx=0, pady=(4, 0))
        self.http_entry = ctk.CTkEntry(effect_tab, width=tab_content_w, height=20)
        self.http_entry.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        self.http_entry.bind("<Return>", lambda e: self.save_current_button())
        self.effect_param_entries = []

        # ---- Misc tab ----
        misc_tab = self.tabview.tab("Misc")
        misc_tab.grid_columnconfigure(0, weight=1, minsize=tab_content_w)
        ctk.CTkLabel(misc_tab, text="Function:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=0, pady=(2, 0))
        self.func_entry = ctk.CTkEntry(misc_tab, width=tab_content_w, height=20)
        self.func_entry.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        self.func_entry.bind("<Return>", lambda e: self.save_current_button())

        # ---- Strips row (fixed at row 3) ----
        strip_row = ctk.CTkFrame(self.right_panel, fg_color="transparent", height=R_STRIPS)
        strip_row.grid(row=3, column=0, sticky="ew", padx=4, pady=0)
        strip_row.grid_propagate(False)
        strip_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(strip_row, text="Strips:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=0, pady=0)
        self.strip_buttons_frame = ctk.CTkFrame(strip_row, fg_color="transparent")
        self.strip_buttons_frame.grid(row=0, column=1, sticky="w", padx=4, pady=0)
        self.strip_buttons = {}
        self.add_strip_btn = ctk.CTkButton(strip_row, text="+", width=24, height=20, fg_color=self.theme["strip_add_remove"], hover_color=self.theme["strip_add_remove_hover"], text_color=self.theme["text_color"], command=self._add_strip_dialog, font=("Arial", 10))
        self.add_strip_btn.grid(row=0, column=2, padx=1, pady=0)
        self.remove_strip_btn = ctk.CTkButton(strip_row, text="−", width=24, height=20, fg_color=self.theme["strip_add_remove"], hover_color=self.theme["strip_add_remove_hover"], text_color=self.theme["text_color"], command=self._remove_current_strip, font=("Arial", 10))
        self.remove_strip_btn.grid(row=0, column=3, padx=0, pady=0)

        self.save_btn = ctk.CTkButton(self.right_panel, text="Save", state="disabled", height=R_SAVE - 2, width=inner_w, command=self.save_current_button, fg_color=self.theme["button"], hover_color=self.theme["button_hover"], text_color="#e0e0e0")
        self.save_btn.grid(row=5, column=0, sticky="ew", padx=4, pady=0)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self._refresh_color_params()
        self._refresh_effect_params()

    def _rebuild_strip_buttons(self):
        for w in self.strip_buttons_frame.winfo_children():
            w.destroy()
        self.strip_buttons.clear()
        for idx in sorted(self.strip_indices):
            is_selected = idx == self.current_strip_index
            btn = ctk.CTkButton(
                self.strip_buttons_frame, text=str(idx), width=26, height=22,
                command=lambda i=idx: self._select_strip(i),
                fg_color=(self.theme["strip_selected"] if is_selected else self.theme["strip_bg"]),
                hover_color=self.theme["strip_hover"],
                text_color=("#e0e0e0" if is_selected else self.theme["text_color"]),
                border_width=2 if is_selected else 0,
                border_color=self.theme["strip_selected_border"],
                font=("Arial", 10)
            )
            btn.pack(side="left", padx=1, pady=0)
            self.strip_buttons[idx] = btn
        self._update_strip_buttons_highlight()

    def _update_strip_buttons_highlight(self):
        for idx, btn in self.strip_buttons.items():
            is_selected = idx == self.current_strip_index
            btn.configure(
                fg_color=self.theme["strip_selected"] if is_selected else self.theme["strip_bg"],
                text_color="#e0e0e0" if is_selected else self.theme["text_color"],
                border_width=2 if is_selected else 0,
            )

    def _select_strip(self, idx):
        """Push current form to strips_data, then load strip idx into form."""
        if self.current_strip_index is not None and self.current_strip_index in self.strips_data:
            self._push_current_strip_to_data()
        self.current_strip_index = idx
        self._load_strip_into_form(idx)
        self._update_strip_labels()
        self._update_strip_buttons_highlight()

    def _update_strip_labels(self):
        s = str(self.current_strip_index) if self.current_strip_index is not None else "—"
        self.color_strip_label.configure(text=f"Color (strip {s}):")
        self.effect_strip_label.configure(text=f"Effect (strip {s}):")

    def _push_current_strip_to_data(self):
        """Write current form (color, effect, misc) into strips_data[current_strip_index]."""
        if self.current_strip_index is None:
            return
        effect_name = self.effect_combo_var.get()
        effect_name = None if effect_name == "None" or not effect_name else effect_name
        color_name = self.color_combo_var.get()
        color_name = None if color_name == "None" or not color_name else color_name
        effect_args = self._collect_param_values(self.effect_param_entries) if effect_name else None
        color_args = self._collect_param_values(self.color_param_entries) if color_name else None
        misc = self.func_entry.get().strip() or None
        self.strips_data[self.current_strip_index] = {
            "effect_name": effect_name, "effect_args": effect_args,
            "color_name": color_name, "color_args": color_args,
            "misc": misc,
        }

    def _ensure_combo_value(self, combo, value):
        """Ensure combo can display value (add to values if missing so loaded configs always show)."""
        vals = list(combo.cget("values"))
        if value and value not in vals:
            combo.configure(values=vals + [value])
        combo.set(value)

    def _load_strip_into_form(self, idx):
        """Load strips_data[idx] into the Color/Effect/Misc form."""
        d = self.strips_data.get(idx, {"effect_name": None, "effect_args": None, "color_name": None, "color_args": None, "misc": None})
        eff = d.get("effect_name") or "None"
        self._ensure_combo_value(self.effect_combo, eff)
        self._refresh_effect_params()
        ea = d.get("effect_args")
        if ea is not None:
            ea = list(ea) if not isinstance(ea, list) else ea
            for i, (pname, entry) in enumerate(self.effect_param_entries):
                if i < len(ea):
                    entry.delete(0, "end")
                    entry.insert(0, str(ea[i]))
        col = d.get("color_name") or "None"
        self._ensure_combo_value(self.color_combo, col)
        self._refresh_color_params()
        ca = d.get("color_args")
        if ca is not None:
            ca = list(ca) if not isinstance(ca, list) else ca
            for i, (pname, entry) in enumerate(self.color_param_entries):
                if i < len(ca):
                    entry.delete(0, "end")
                    entry.insert(0, str(ca[i]))
        self.func_entry.delete(0, "end")
        self.func_entry.insert(0, d.get("misc") or "")

    def _add_strip_dialog(self):
        available = [i for i in range(self.num_strips) if i not in self.strip_indices]
        if not available:
            return  # could show a message
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add strip")
        dialog.geometry("240x160")
        dialog.transient(self)

        ctk.CTkLabel(dialog, text="Strip index:").pack(pady=(20, 8))
        combo = ctk.CTkComboBox(dialog, values=[str(i) for i in available], width=200)
        combo.pack(pady=8)
        combo.set(str(available[0]))

        def ok():
            idx = int(combo.get())
            if idx not in self.strip_indices:
                self.strip_indices.append(idx)
                self.strip_indices.sort()
                self.strips_data[idx] = {"effect_name": None, "effect_args": None, "color_name": None, "color_args": None, "misc": None}
                self._rebuild_strip_buttons()
                self._select_strip(idx)
            dialog.destroy()

        ok_btn = ctk.CTkButton(dialog, text="OK", width=80, command=ok, text_color=self.theme["text_color"])
        ok_btn.pack(pady=15)
        dialog.bind("<Return>", lambda e: ok())
        dialog.focus_set()
        combo.focus_set()

    def _remove_current_strip(self):
        if self.current_strip_index is None or not self.strip_indices:
            return
        self._push_current_strip_to_data()
        self.strip_indices = [i for i in self.strip_indices if i != self.current_strip_index]
        del self.strips_data[self.current_strip_index]
        self._rebuild_strip_buttons()
        if self.strip_indices:
            self._select_strip(self.strip_indices[0])
        else:
            self.current_strip_index = None
            self._update_strip_labels()
            self.effect_combo_var.set("None")
            self.color_combo_var.set("None")
            self._refresh_effect_params()
            self._refresh_color_params()
            self.func_entry.delete(0, "end")

    def _set_temp_color(self, color_code):
        self.temp_selected_color = color_code
        self.selected_color_preview.configure(text=str(color_code), text_color=self.color_palette[color_code])
        for code, btn in self.palette_buttons.items():
            btn.configure(border_width=1 if code == color_code else 0, border_color=self.theme["palette_border"])

    def _build_grid(self):
        btn_size = self.grid_size // 9
        for r in range(9):
            for c in range(9):
                btn = ctk.CTkButton(
                    self.launchpad_frame, text="", width=btn_size, height=btn_size,
                    corner_radius=0, border_width=1, border_color=self.theme["button_border"],
                    fg_color=self.theme["button"], hover_color=self.theme["button"],
                    command=lambda row=r, col=c: self._select_button(row, col)
                )
                btn.place(x=c * btn_size, y=(8 - r) * btn_size)
                self.buttons[r][c] = btn

    def _select_button(self, row, col):
        self.selected_coords = (row, col)
        # Clear current strip so _select_strip() won't push previous button's form into the new strips_data
        self.current_strip_index = None
        data = self.grid[row][col]
        self.edit_label.configure(text=f"Button: {row}, {col}")
        self.save_btn.configure(state="normal")

        # Button color and active
        self.temp_selected_color = data[0]
        self._set_temp_color(data[0])
        self.on_var.set(data[1])

        # HTTP (global per button)
        self.http_entry.delete(0, "end")
        self.http_entry.insert(0, data[2] if data[2] is not None else "")

        # Parse UDP for all strips
        parsed = _parse_udp_all_strips(data[3])
        if parsed:
            self.strip_indices = sorted({t[0] for t in parsed})
            self.strips_data = {}
            for idx, ef_name, ea, cf_name, ca, misc in parsed:
                # Backward compat: if single strip and no misc in UDP, use button's global func
                if misc is None and len(parsed) == 1 and data[4]:
                    misc = data[4]
                self.strips_data[idx] = {
                    "effect_name": ef_name, "effect_args": ea,
                    "color_name": cf_name, "color_args": ca,
                    "misc": misc,
                }
        else:
            # No strips in UDP: start with strip 0
            self.strip_indices = [0]
            self.strips_data = {0: {"effect_name": None, "effect_args": None, "color_name": None, "color_args": None, "misc": data[4] if data[4] is not None else None}}

        self._rebuild_strip_buttons()
        if self.strip_indices:
            self._select_strip(self.strip_indices[0])
        else:
            self.current_strip_index = None
            self._update_strip_labels()

        self._update_grid_button_highlight()

    def _update_grid_button_highlight(self):
        """Outline the selected grid cell with a white border."""
        sr, sc = self.selected_coords
        for r in range(9):
            for c in range(9):
                btn = self.buttons[r][c]
                if (r, c) == (sr, sc):
                    btn.configure(border_width=2, border_color="#ffffff")
                else:
                    btn.configure(border_width=1, border_color=self.theme["button_border"])

    def _collect_param_values(self, entries_holder):
        """Collect non-blank param values in order. Blank -> omit from list."""
        out = []
        for pname, entry in entries_holder:
            v = _parse_param_value(entry.get() if entry.winfo_exists() else "")
            if v is not None:
                out.append(v)
        return out if out else None

    def save_current_button(self):
        row, col = self.selected_coords
        new_color = self.temp_selected_color
        new_on = self.on_var.get()
        http_val = self.http_entry.get().strip() or None

        # Push current form into strips_data before building UDP
        self._push_current_strip_to_data()

        # Build UDP from all strips (each command can have 6th element misc)
        parts = []
        for idx in sorted(self.strip_indices):
            d = self.strips_data.get(idx, {})
            ef = d.get("effect_name") or "None"
            ea = _args_to_udp_part(d.get("effect_args"))
            cf = d.get("color_name") or "None"
            ca = _args_to_udp_part(d.get("color_args"))
            misc = d.get("misc")
            misc_str = repr(misc) if misc else "None"
            parts.append(f"[{idx}, {ef}, {ea}, {cf}, {ca}, {misc_str}]")
        udp_val = "[" + ", ".join(parts) + "]"

        # Per-strip misc is in UDP; top-level func kept for compatibility (None when using strips)
        func_val = None
        new_data = [new_color, new_on, http_val, udp_val, func_val]
        self.grid[row][col] = new_data
        if self.lp is not None:
            self.lp.grid[row][col] = new_data
        if self.current_file_path:
            try:
                with open(self.current_file_path, "w") as f:
                    json.dump(self.grid, f, indent=4)
            except OSError as e:
                print(f"Error saving config: {e}")
            if self.lp is not None:
                self.lp.save_grid_to_file(self.current_file_path)

    def sync(self, bpm=None):
        if bpm is not None:
            self.bpm = bpm
            self.bpm_label.configure(text=str(int(round(bpm))))
        # Use GUI-owned grid for button colors (works with or without Launchpad connected)
        for r in range(9):
            for c in range(9):
                color_code, is_on, _, __, ___ = self.grid[r][c]
                target_hex = self.color_palette.get(color_code, "#FFFFFF") if is_on else self.theme["button_off"]
                btn = self.buttons[r][c]
                if btn.cget("fg_color") != target_hex:
                    btn.configure(fg_color=target_hex, hover_color=target_hex)
        self._update_grid_button_highlight()
        self.update_idletasks()
        self.update()