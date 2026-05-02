# Detailed System Architecture & Workflow

## 1. Introduction & High-Level Concept
The **Generative AI-Based Automated 3D CAD Model Generator** bridges the gap between human engineering intent and strict parametric 3D modeling. Traditional CAD software requires engineers to manually draw 2D sketches and extrude them into 3D. This system automates the entire process for API 6A standard components (flanges, bonnets, tees, etc.) by converting **natural language prompts** into **mathematically exact 3D solid models (STEP files)**.

---

## 2. Complete Workflow & Data Transfer Lifecycle
What happens the exact millisecond a user types a prompt (e.g., *"give me a 3-1/16 blind flange rated for 10k"*) and presses Enter?

### Stage A: Natural Language Understanding (NLU) Routing
1. **Input:** The raw string is sent from the GUI or CLI to `main.py -> extract_request()`.
2. **Groq LLM (Cloud):** The string is sent to the Groq API (llama-3.1-8b-instant). A rigid system prompt forces the LLM to return a clean JSON object. Groq acts as a hyper-fast semantic router, understanding that "3-1/16" means `3.0625` and "10k" means `10000`.
3. **Ollama LLM (Local Fallback):** If Groq fails (no internet, missing API key), the same request is routed to a local `llama3` instance.
4. **Regex (Failsafe):** If no LLM is available, a robust regex engine attempts to extract the size and pressure.
5. **Output:** The chaotic string is transformed into a strict tuple: `part="blind"`, `size=3.0625`, `pressure=10000`.

### Stage B: Data Lookup & Matrix Filtering
1. **Pandas Query:** The tuple is passed to `load_dimensions()`. Pandas loads `data/api6a.csv` into a DataFrame.
2. **Matrix Filtering:** It queries the dataset for the exact match. 
3. **Fuzzy Matching:** If the user asked for a size that doesn't exist (e.g., 3.5"), `find_closest_match()` computes a weighted mathematical distance across the entire dataset to suggest the top 3 closest API 6A standard sizes.
4. **Output:** A Python dictionary containing ~20 specific engineering dimensions (e.g., `{"flange_od": 300, "bolt_count": 8, "flange_thk": 40}`).

### Stage C: Parametric Override (GUI Only)
1. **UI Population:** The dictionary populates the UI sliders. 
2. **User Intervention:** The user can manually drag a slider to increase the `flange_od` from 300mm to 310mm.
3. **Output:** A modified dictionary of dimensions.

### Stage D: Topological 3D Construction
1. **Routing:** `build_model()` checks the part type (`blind`) and routes the dictionary to the specific builder module: `model/blind.py`.
2. **CadQuery Execution:** The script sequentially builds a 3D Boundary Representation (B-Rep) solid. It sketches a circle, extrudes it by `flange_thk`, selects the top face, and drills `bolt_count` holes in a polar array.
3. **Output:** A mathematical `cq.Workplane` solid in system memory.

### Stage E: Cost Estimation & File Export
1. **Estimation:** The `calculate_weight_cost()` function measures the exact millimeter volume of the solid using `.val().Volume()`. It multiplies this by the user-selected material density (e.g., Carbon Steel) to get Weight, and multiplies the weight by the market rate to get the exact Cost in INR (₹).
2. **Serialization:** The solid is exported to the `output/` directory as an ISO 10303 STEP file, ready for CNC manufacturing or Finite Element Analysis (FEA).

---

## 3. Significance of Libraries

Every library in `requirements.txt` was chosen for a specific architectural purpose:

*   **`cadquery`:** The backbone of the project. It builds mathematical B-Rep solids rather than visual meshes (like Blender). This is critical because oil & gas components require mathematically perfect circles and cylinders for CNC machining and stress analysis.
*   **`pandas`:** The data engine. Parsing a massive CSV with native Python loops is slow and error-prone. Pandas instantly vectorizes the dataset, making the Fuzzy Matching algorithm (calculating distance metrics across 130+ rows) instantaneous.
*   **`groq` & `ollama`:** These replace rigid dropdown menus. They allow the software to understand human intent, making the tool accessible to engineers who might use shorthand or colloquial formatting.
*   **`tkinter`:** The built-in Python GUI framework. Chosen because it requires zero web servers, zero browser dependencies, and creates a fast, native desktop executable that can safely read/write local STEP files.
*   **`ezdxf`:** Used in `drawing/dxf_parser.py` to extract dimensions directly from 2D AutoCAD files, proving the architecture can ingest data from sources other than natural language.

---

## 4. Significance of CSV Data Files

### `data/api6a.csv` (The Brain)
This file is the ultimate source of truth for the entire application. 
*   **Why a CSV?** A CSV was chosen over an SQLite database or hardcoded Python dictionaries because engineers and drafters live in Excel. If a new API 6A standard is released, or a company wants to add proprietary parts, an engineer can simply open the CSV in Excel, add a row, and save it. The Python code automatically detects the new row instantly.
*   **Structure:** It contains 24 columns mapping exact sizes (1-13/16" to 7-1/16") and pressures (2000 to 20000 PSI) to physical dimensions (`flange_od`, `bore`, `bolt_count`).

### `data/batch_jobs.csv`
An experimental file proving the architecture can handle automated bulk-generation. A user can define 500 parts in this CSV, and a script could loop through it, generating 500 STEP files unattended.

---

## 5. Detailed File-by-File Breakdown

The repository is structured to strictly separate concerns: data, geometry, orchestration, interfaces, and testing. Here is a detailed look at every single file in the project and its exact role:

### Root Directory (Configuration & Orchestration)
*   **`main.py`:** The "Brain" and Orchestrator. This is the largest and most important file. It contains the logic to route LLM requests to Groq or Ollama, parse regex fallbacks, load the Pandas DataFrame, execute the fuzzy matching algorithm, compute the material weight/cost mathematics, and finally trigger the specific CadQuery geometry builders.
*   **`cli.py`:** The Terminal Interface. A lightweight argparse script that imports `main.py`. It handles terminal arguments like `--prompt`, `--list`, and the interactive REPL loop. It acts as the pipeline's "mouth" for command-line users.
*   **`requirements.txt`:** The dependency ledger. Lists all pip packages (`cadquery`, `pandas`, `groq`, `ollama`, `ezdxf`, etc.) required to build the environment.
*   **`.env` & `.env.example`:** Environment configuration. Holds sensitive keys like `GROQ_API_KEY`. `.env.example` is pushed to GitHub as a template, while `.env` is ignored.
*   **`.gitignore`:** Source control filter. Ensures the virtual environment, pytest caches, and generated `.step` files are not pushed to GitHub.
*   **`README.md`:** The user-facing manual. High-level instructions on installation, CLI/GUI usage, and supported features.
*   **`ARCHITECTURE.md`:** (This file) The developer-facing manual detailing deep system internals and data flow.

### `ui/` Directory (Frontend)
*   **`app.py`:** The Graphical User Interface. Built with Tkinter, this file renders the dark-themed application window. It manages state (what is currently typed, which material is selected) and dynamically generates a scrollable list of sliders depending on the dictionary returned by `main.py`. It runs entirely locally on the host machine.

### `data/` Directory (The Source of Truth)
*   **`api6a.csv`:** The Master Engineering Dataset. Contains 136 distinct configurations mapping 6 part types to sizes (1-13/16" to 7-1/16") and pressures (2000 to 20000 PSI) with 24 specific engineering dimension columns.
*   **`batch_jobs.csv`:** An experimental batch-generation template to prove the architecture can ingest bulk configurations instead of single prompts.

### `model/` Directory (The Geometry Hands)
These files know *nothing* about AI, datasets, or user interfaces. They are pure mathematical functions that take arguments (like `flange_od` and `bore`) and return a `cq.Workplane` 3D solid.
*   **`__init__.py`:** Identifies the folder as a Python module.
*   **`bonnet.py`:** Builds a 3-tier cylinder (flange, hub, body) with a through-bore, bolt holes, and optional seal grooves/counterbores.
*   **`flange.py`:** Builds a simple disk with a bore and bolt circle.
*   **`spool.py`:** Uses `build_flange` twice and connects them with a central pipe cylinder.
*   **`blind.py`:** Builds a solid disk identical to a flange, but explicitly omits the through-bore.
*   **`tee.py`:** Builds a 3-way intersection by building a spool on the X/Z axis, and merging a perpendicular branch pipe and flange on the Y axis.
*   **`gasket.py`:** Builds a metallic sealing ring by drawing an octagonal or rectangular 2D cross-section and revolving it 360 degrees around the Z axis.

### `drawing/` Directory (Experimental Utils)
*   **`dxf_parser.py`:** A utility script using `ezdxf`. It parses 2D AutoCAD files, hunting for text entities in the format `KEY=VALUE` (e.g., `BORE=52`), proving that the system can ingest dimensional data directly from drafting files.

### `tests/` Directory (The Immune System)
The pytest suite ensures that adding new features doesn't break existing logic.
*   **`__init__.py`:** Identifies the folder as a test module.
*   **`test_parsers.py`:** Tests the NLU regex fallbacks. Ensures fractions (`3-1/16` -> `3.0625`), pressures (`10k` -> `10000`), and all 6 part names are parsed perfectly.
*   **`test_dataset.py`:** Tests data integrity. Checks that the CSV exists, contains no `NaN` values in critical columns, has at least 100 rows, covers all 6 part families, and successfully loads dimensions for each type.
*   **`test_fuzzy.py`:** Tests the matching algorithm. Asserts that an exact match returns a distance of 0, and that extreme typos correctly route to the nearest logical API 6A size.

### `output/` Directory
*   **`.gitkeep`:** A blank file that forces Git to track the empty folder. All generated `.step` files are dumped into this directory to keep the project root perfectly clean.

---

## 6. Comprehensive Feature Deep-Dive

*   **Multi-Agent Fallback System:** If Groq's servers go down, the software doesn't crash; it silently falls back to Ollama. If Ollama isn't installed, it falls back to Regex. This guarantees 100% uptime for the user.
*   **Fuzzy Search Mathematics:** If an engineer asks for a "3.5 inch 12000 PSI bonnet", it doesn't exist in the API 6A spec. The system calculates a weighted penalty score: `Delta Size + (Delta Pressure / Max Pressure)`. It then offers the user a 10,000 PSI or 15,000 PSI alternative, acting as a smart engineering assistant rather than a dumb error-thrower.
*   **Dynamic Parametric Overrides:** The UI doesn't just generate a file; it acts as a staging ground. By pulling the data into sliders *before* generation, an engineer can use the API 6A specs as a starting template, but tweak the `flange_od` to fit a custom machine, giving them total control.
*   **Dynamic Material Intelligence:** The software calculates the volume mathematically from the 3D topology. Changing the dropdown from Aluminum to Inconel 718 instantly recalculates the mass (from 2,700 kg/m³ to 8,190 kg/m³) and the cost (from ₹250/kg to ₹2500/kg), giving supply chain managers instant raw material forecasting without needing to open a separate calculator.
