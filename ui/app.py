import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Ensure project root is on path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    generate_from_prompt,
    generate_from_dims,
    list_supported,
    extract_request,
    load_dimensions,
    find_closest_match,
    build_model,
    calculate_weight_cost,
    MATERIALS,
)


# -------------------- COLOUR PALETTE --------------------
BG_DARK = "#1e1e2e"
BG_MID = "#2a2a3d"
BG_CARD = "#313147"
FG_TEXT = "#cdd6f4"
FG_DIM = "#9399b2"
ACCENT = "#89b4fa"
ACCENT_HOVER = "#74c7ec"
SUCCESS = "#a6e3a1"
ERROR = "#f38ba8"
WARN = "#fab387"
BORDER = "#45475a"


# -------------------- THEMED WIDGETS --------------------

class ThemedLabel(tk.Label):
    def __init__(self, master, **kw):
        defaults = {"bg": BG_DARK, "fg": FG_TEXT, "font": ("Segoe UI", 10)}
        defaults.update(kw)
        super().__init__(master, **defaults)


class ThemedButton(tk.Button):
    def __init__(self, master, **kw):
        defaults = {
            "bg": ACCENT,
            "fg": "#1e1e2e",
            "activebackground": ACCENT_HOVER,
            "activeforeground": "#1e1e2e",
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat",
            "cursor": "hand2",
            "padx": 16,
            "pady": 6,
            "bd": 0,
        }
        defaults.update(kw)
        super().__init__(master, **defaults)
        self.bind("<Enter>", lambda e: self.config(bg=ACCENT_HOVER))
        self.bind("<Leave>", lambda e: self.config(bg=kw.get("bg", ACCENT)))


class ThemedEntry(tk.Entry):
    def __init__(self, master, **kw):
        defaults = {
            "bg": BG_MID,
            "fg": FG_TEXT,
            "insertbackground": ACCENT,
            "font": ("Segoe UI", 10),
            "relief": "flat",
            "highlightthickness": 1,
            "highlightcolor": ACCENT,
            "highlightbackground": BORDER,
        }
        defaults.update(kw)
        super().__init__(master, **defaults)


# -------------------- MAIN APP --------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("API 6A CAD Model Generator")
        self.geometry("960x780")
        self.minsize(860, 700)
        self.configure(bg=BG_DARK)

        # State
        self._current_part = None
        self._current_size = None
        self._current_pressure = None
        self._current_dims = None
        self._current_model = None
        self._dim_vars = {}  # dimension_name -> tk.DoubleVar / tk.IntVar

        self._build_ui()

    def _build_ui(self):
        # ---- Header ----
        header_frame = tk.Frame(self, bg=BG_DARK, pady=10)
        header_frame.pack(fill="x")

        title = tk.Label(
            header_frame,
            text="API 6A CAD Model Generator",
            font=("Segoe UI", 18, "bold"),
            bg=BG_DARK,
            fg=ACCENT,
        )
        title.pack()

        subtitle = tk.Label(
            header_frame,
            text="Prompt  ->  Dataset  ->  Parametric Tuning  ->  3D CAD  ->  STEP",
            font=("Segoe UI", 10),
            bg=BG_DARK,
            fg=FG_DIM,
        )
        subtitle.pack()

        # ---- Main container ----
        main = tk.Frame(self, bg=BG_DARK, padx=16, pady=4)
        main.pack(fill="both", expand=True)

        # ---- Prompt Section ----
        prompt_card = tk.LabelFrame(
            main,
            text="  Prompt Input  ",
            font=("Segoe UI", 11, "bold"),
            bg=BG_CARD,
            fg=ACCENT,
            padx=14,
            pady=10,
            relief="flat",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        prompt_card.pack(fill="x", pady=(0, 8))

        ThemedLabel(prompt_card, text="Enter a natural language prompt:", bg=BG_CARD).pack(anchor="w")

        self.prompt_entry = ThemedEntry(prompt_card, width=100)
        self.prompt_entry.pack(pady=6, fill="x")
        self.prompt_entry.insert(0, "Generate API 6A 2-1/16 10k PSI bonnet")
        self.prompt_entry.bind("<Return>", lambda e: self.on_parse())

        btn_row = tk.Frame(prompt_card, bg=BG_CARD)
        btn_row.pack(fill="x", pady=4)

        self.parse_btn = ThemedButton(btn_row, text="1. Parse & Lookup", command=self.on_parse)
        self.parse_btn.pack(side="left")

        self.generate_btn = ThemedButton(btn_row, text="2. Generate STEP", command=self.on_generate, bg="#45475a", state="disabled")
        self.generate_btn.pack(side="left", padx=10)

        self.supported_btn = ThemedButton(btn_row, text="Show Supported Sizes", command=self.on_show_supported, bg=BG_MID, fg=FG_TEXT)
        self.supported_btn.pack(side="left", padx=4)

        self.clear_btn = ThemedButton(
            btn_row,
            text="Clear",
            command=lambda: self.prompt_entry.delete(0, tk.END),
            bg=BG_MID,
            fg=FG_TEXT,
        )
        self.clear_btn.pack(side="left", padx=4)

        # ---- Quick Samples Row ----
        sample_row = tk.Frame(prompt_card, bg=BG_CARD)
        sample_row.pack(fill="x", pady=(8, 0))

        ThemedLabel(sample_row, text="Quick Samples:", bg=BG_CARD, font=("Segoe UI", 9, "italic"), fg=FG_DIM).pack(side="left", padx=(0, 6))

        samples = [
            ("Bonnet", "Generate API 6A bonnet 3-1/16 10k PSI"),
            ("Flange", "flange 4-1/16 5000"),
            ("Spool", "spool 2-1/16 15000"),
            ("Blind", "blind flange 3-1/16 10k"),
            ("Tee", "tee 3-1/16 10k"),
            ("Gasket", "ring gasket 2-1/16 10k"),
        ]
        for label, prompt in samples:
            btn = ThemedButton(
                sample_row,
                text=label,
                bg=BG_MID,
                fg=FG_TEXT,
                font=("Segoe UI", 9),
                padx=8,
                pady=2,
                command=lambda p=prompt: (self.prompt_entry.delete(0, tk.END), self.prompt_entry.insert(0, p)),
            )
            btn.pack(side="left", padx=3)

        # ---- Material & Weight Section ----
        material_card = tk.LabelFrame(
            main,
            text="  Material & Weight Estimator  ",
            font=("Segoe UI", 11, "bold"),
            bg=BG_CARD,
            fg=ACCENT,
            padx=14,
            pady=8,
            relief="flat",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        material_card.pack(fill="x", pady=(0, 8))

        mat_row = tk.Frame(material_card, bg=BG_CARD)
        mat_row.pack(fill="x")

        ThemedLabel(mat_row, text="Material:", bg=BG_CARD, font=("Segoe UI", 10)).pack(side="left")

        self.material_var = tk.StringVar(value="Carbon Steel (A105)")
        material_names = list(MATERIALS.keys())
        self.material_combo = ttk.Combobox(
            mat_row,
            textvariable=self.material_var,
            values=material_names,
            state="readonly",
            width=28,
            font=("Segoe UI", 10),
        )
        self.material_combo.pack(side="left", padx=10)

        # Style the combobox
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=BG_MID, background=BG_MID, foreground=FG_TEXT)

        self.weight_label = ThemedLabel(
            mat_row,
            text="  Weight: --  |  Volume: --  |  Est. Cost: --",
            bg=BG_CARD,
            fg=FG_DIM,
            font=("Segoe UI", 10),
        )
        self.weight_label.pack(side="left", padx=10)

        # ---- Parametric Sliders Section ----
        self.slider_card = tk.LabelFrame(
            main,
            text="  Parametric Dimensions (editable)  ",
            font=("Segoe UI", 11, "bold"),
            bg=BG_CARD,
            fg=ACCENT,
            padx=14,
            pady=10,
            relief="flat",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.slider_card.pack(fill="both", expand=True, pady=(0, 8))

        # Scrollable frame for sliders
        self.slider_canvas = tk.Canvas(self.slider_card, bg=BG_CARD, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.slider_card, orient="vertical", command=self.slider_canvas.yview)
        self.slider_inner = tk.Frame(self.slider_canvas, bg=BG_CARD)

        self.slider_inner.bind(
            "<Configure>",
            lambda e: self.slider_canvas.configure(scrollregion=self.slider_canvas.bbox("all")),
        )
        self.slider_canvas.create_window((0, 0), window=self.slider_inner, anchor="nw")
        self.slider_canvas.configure(yscrollcommand=scrollbar.set)

        self.slider_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mousewheel scrolling
        self.slider_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.slider_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        # Placeholder text
        self._placeholder = ThemedLabel(
            self.slider_inner,
            text="Click '1. Parse & Lookup' to load dimensions here...",
            fg=FG_DIM,
            bg=BG_CARD,
            font=("Segoe UI", 10, "italic"),
        )
        self._placeholder.pack(pady=30)

        # ---- Status / Output ----
        status_card = tk.LabelFrame(
            main,
            text="  Status / Output  ",
            font=("Segoe UI", 11, "bold"),
            bg=BG_CARD,
            fg=ACCENT,
            padx=14,
            pady=10,
            relief="flat",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        status_card.pack(fill="x", pady=(0, 8))

        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = tk.Label(
            status_card,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            bg=BG_CARD,
            fg=SUCCESS,
            anchor="w",
        )
        self.status_label.pack(fill="x")

        # Progress bar
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=BG_MID,
            background=ACCENT,
            darkcolor=ACCENT,
            lightcolor=ACCENT_HOVER,
            bordercolor=BG_CARD,
        )
        self.progress = ttk.Progressbar(
            status_card,
            style="Custom.Horizontal.TProgressbar",
            mode="indeterminate",
            length=300,
        )
        self.progress.pack(fill="x", pady=(4, 0))

        self.output_text = tk.Text(
            status_card,
            height=5,
            wrap="word",
            bg=BG_MID,
            fg=FG_TEXT,
            font=("Consolas", 9),
            relief="flat",
            insertbackground=ACCENT,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.output_text.pack(fill="x", pady=(6, 0))

        # ---- Footer ----
        footer = tk.Label(
            self,
            text="Supports: bonnet, flange, spool, blind flange, tee, ring gasket  |  Tip: Add new sizes to data/api6a.csv",
            font=("Segoe UI", 9),
            bg=BG_DARK,
            fg=FG_DIM,
        )
        footer.pack(pady=6)

    # -------------------- HELPERS --------------------

    def log(self, msg: str):
        self.output_text.insert(tk.END, msg + "\n")
        self.output_text.see(tk.END)

    def set_status(self, msg: str, color=None):
        self.status_var.set(msg)
        self.status_label.config(fg=color or SUCCESS)
        self.update_idletasks()

    def _clear_sliders(self):
        for widget in self.slider_inner.winfo_children():
            widget.destroy()
        self._dim_vars.clear()

    def _build_sliders(self, dims: dict, part: str):
        """Build slider rows for each editable dimension."""
        self._clear_sliders()

        # Determine which keys are relevant per part
        part_keys = {
            "bonnet": [
                "body_od", "body_height", "bore", "flange_od", "flange_thk",
                "hub_od", "hub_height", "bolt_circle_dia", "bolt_hole_dia",
                "bolt_count", "fillet_r", "counterbore_dia", "counterbore_depth",
                "seal_groove_dia", "seal_groove_width", "seal_groove_depth",
            ],
            "flange": [
                "flange_od", "flange_thk", "bore", "bolt_circle_dia",
                "bolt_hole_dia", "bolt_count", "fillet_r",
            ],
            "spool": [
                "flange_od", "flange_thk", "bore", "bolt_circle_dia",
                "bolt_hole_dia", "bolt_count", "spool_length", "fillet_r",
            ],
            "blind": [
                "flange_od", "flange_thk", "bolt_circle_dia",
                "bolt_hole_dia", "bolt_count", "fillet_r",
                "seal_groove_dia", "seal_groove_width", "seal_groove_depth",
            ],
            "tee": [
                "flange_od", "flange_thk", "bore", "bolt_circle_dia",
                "bolt_hole_dia", "bolt_count", "spool_length", "branch_length", "fillet_r",
            ],
            "gasket": [
                "gasket_od", "gasket_id", "gasket_height",
            ],
        }
        relevant = part_keys.get(part, list(dims.keys()))

        # Friendly display names
        display_names = {
            "body_od": "Body OD (mm)",
            "body_height": "Body Height (mm)",
            "bore": "Bore (mm)",
            "flange_od": "Flange OD (mm)",
            "flange_thk": "Flange Thickness (mm)",
            "hub_od": "Hub OD (mm)",
            "hub_height": "Hub Height (mm)",
            "bolt_circle_dia": "Bolt Circle Dia (mm)",
            "bolt_hole_dia": "Bolt Hole Dia (mm)",
            "bolt_count": "Bolt Count",
            "fillet_r": "Fillet Radius (mm)",
            "counterbore_dia": "Counterbore Dia (mm)",
            "counterbore_depth": "Counterbore Depth (mm)",
            "seal_groove_dia": "Seal Groove Dia (mm)",
            "seal_groove_width": "Seal Groove Width (mm)",
            "seal_groove_depth": "Seal Groove Depth (mm)",
            "spool_length": "Spool Length (mm)",
            "branch_length": "Branch Length (mm)",
            "gasket_od": "Gasket OD (mm)",
            "gasket_id": "Gasket ID (mm)",
            "gasket_height": "Gasket Height (mm)",
        }

        for key in relevant:
            if key not in dims:
                continue
            val = dims[key]

            row = tk.Frame(self.slider_inner, bg=BG_CARD)
            row.pack(fill="x", pady=2)

            label_text = display_names.get(key, key)
            label = ThemedLabel(row, text=f"{label_text}:", width=24, anchor="w", bg=BG_CARD)
            label.pack(side="left")

            if key == "bolt_count":
                var = tk.IntVar(value=int(val))
                spinbox = tk.Spinbox(
                    row,
                    from_=2,
                    to=24,
                    textvariable=var,
                    width=8,
                    bg=BG_MID,
                    fg=FG_TEXT,
                    font=("Segoe UI", 10),
                    buttonbackground=BG_MID,
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=BORDER,
                )
                spinbox.pack(side="left", padx=(0, 10))
            else:
                var = tk.DoubleVar(value=float(val))
                max_val = max(float(val) * 2.0, 10.0)
                resolution = 0.1 if val < 20 else 1.0

                scale = tk.Scale(
                    row,
                    from_=0,
                    to=max_val,
                    resolution=resolution,
                    orient="horizontal",
                    variable=var,
                    length=280,
                    bg=BG_CARD,
                    fg=FG_TEXT,
                    troughcolor=BG_MID,
                    highlightthickness=0,
                    font=("Segoe UI", 8),
                    activebackground=ACCENT,
                    sliderrelief="flat",
                )
                scale.pack(side="left", padx=(0, 6))

                # Direct entry for precision
                entry = ThemedEntry(row, textvariable=var, width=10)
                entry.pack(side="left")

            self._dim_vars[key] = var

    def _update_weight_display(self):
        """Calculate and display weight/cost for the current model."""
        if self._current_model is None:
            self.weight_label.config(text="  Weight: --  |  Volume: --  |  Est. Cost: --")
            return

        material = self.material_var.get()
        try:
            result = calculate_weight_cost(self._current_model, material)
            self.weight_label.config(
                text=(
                    f"  Weight: {result['weight_kg']:.3f} kg  |  "
                    f"Volume: {result['volume_cm3']:.1f} cm3  |  "
                    f"Est. Cost: ${result['cost_usd']:.2f} USD"
                ),
                fg=SUCCESS,
            )
        except Exception as e:
            self.weight_label.config(text=f"  Error calculating weight: {e}", fg=ERROR)

    # -------------------- ACTIONS --------------------

    def on_parse(self):
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt.")
            return

        try:
            self.set_status("Parsing prompt...", WARN)
            self.progress.start(15)
            self.log(f"> Parsing: {prompt}")

            part, size_inch, pressure_psi = extract_request(prompt)
            self.log(f"  Detected: part={part}, size={size_inch}\", pressure={pressure_psi} PSI")

            try:
                dims = load_dimensions(part, size_inch, pressure_psi)
            except ValueError as e:
                # Fuzzy match fallback
                error_msg = str(e)
                self.log(f"  [WARN] {error_msg}")

                suggestions = find_closest_match(part, size_inch, pressure_psi)
                if suggestions:
                    best = suggestions[0]
                    msg = (
                        f"No exact match for {part} {size_inch}\" @ {pressure_psi} PSI.\n\n"
                        f"Closest available:\n"
                    )
                    for s in suggestions[:3]:
                        msg += f"  - {s['part']} {s['size']}\" @ {s['pressure']} PSI\n"
                    msg += f"\nUse closest match ({best['part']} {best['size']}\" @ {best['pressure']} PSI)?"

                    if messagebox.askyesno("Fuzzy Match", msg):
                        part = best["part"]
                        size_inch = best["size"]
                        pressure_psi = best["pressure"]
                        dims = load_dimensions(part, size_inch, pressure_psi)
                        self.log(f"  Using: {part} {size_inch}\" @ {pressure_psi} PSI")
                    else:
                        self.set_status("Cancelled.", FG_DIM)
                        self.progress.stop()
                        return
                else:
                    raise

            self._current_part = part
            self._current_size = size_inch
            self._current_pressure = pressure_psi
            self._current_dims = dims
            self._current_model = None

            self._build_sliders(dims, part)

            self.generate_btn.config(state="normal", bg=ACCENT)
            self.weight_label.config(text="  Weight: --  |  Volume: --  |  Est. Cost: --  (generate to calculate)", fg=FG_DIM)
            self.set_status(
                f"Loaded: {part} {size_inch}\" @ {pressure_psi} PSI  --  Adjust dimensions, then click 'Generate STEP'",
                SUCCESS,
            )
            self.log(f"  Dimensions loaded ({len(dims)} parameters). Ready to generate.")

        except Exception as e:
            self.set_status("Parse failed", ERROR)
            self.log(f"  [ERROR] {e}")
            messagebox.showerror("Parse Error", str(e))
        finally:
            self.progress.stop()

    def on_generate(self):
        if self._current_dims is None:
            messagebox.showerror("Error", "Please parse a prompt first.")
            return

        try:
            self.generate_btn.config(state="disabled")
            self.set_status("Generating STEP... please wait", WARN)
            self.progress.start(15)

            # Collect potentially modified dimensions from sliders
            final_dims = dict(self._current_dims)
            for key, var in self._dim_vars.items():
                try:
                    final_dims[key] = var.get()
                except Exception:
                    pass

            self.log(f"> Generating {self._current_part} STEP...")

            # Build the model first (for weight calc)
            self._current_model = build_model(self._current_part, final_dims)

            # Export to STEP
            from main import export_step, unique_step_name, OUT_DIR
            out_name = unique_step_name(self._current_part, self._current_size, self._current_pressure)
            out_path = export_step(self._current_model, OUT_DIR / out_name)

            self.log(f"  [SUCCESS] STEP created: {out_path}")

            # Calculate and display weight/cost
            self._update_weight_display()

            material = self.material_var.get()
            try:
                result = calculate_weight_cost(self._current_model, material)
                self.log(
                    f"  Material: {material}  |  Weight: {result['weight_kg']:.3f} kg  |  "
                    f"Volume: {result['volume_cm3']:.1f} cm3  |  Est. Cost: ${result['cost_usd']:.2f}"
                )
            except Exception:
                pass

            self.set_status("Done -- STEP file saved!", SUCCESS)
            messagebox.showinfo("Success", f"STEP file created:\n{out_path}")

        except Exception as e:
            self.set_status("Generation failed", ERROR)
            self.log(f"  [ERROR] {e}")
            messagebox.showerror("Generation Failed", str(e))
        finally:
            self.generate_btn.config(state="normal")
            self.progress.stop()

    def on_show_supported(self):
        try:
            df = list_supported()
            text = df.to_string(index=False)
            self.log("\n--- Supported Configurations ---")
            self.log(text)
            self.log(f"--- Total: {len(df)} configurations ---\n")
            self.set_status(f"Loaded {len(df)} supported configurations", SUCCESS)
        except Exception as e:
            self.set_status("Error reading dataset", ERROR)
            self.log(f"  [ERROR] {e}")
            messagebox.showerror("Dataset Error", str(e))


if __name__ == "__main__":
    # Better DPI scaling on Windows
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = App()
    app.mainloop()
