# Generative AI-Based Automated 3D CAD Model Generator

> An intelligent, AI-powered tool that converts **natural language prompts** into production-ready **3D CAD STEP files** for API 6A oil & gas components. Powered by CadQuery, Groq LLM, and a parametric Tkinter interface.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Workflow](#architecture--workflow)
3. [Supported Part Types](#supported-part-types)
4. [Dataset Reference](#dataset-reference)
5. [AI Parsing Pipeline](#ai-parsing-pipeline)
6. [Fuzzy Matching Engine](#fuzzy-matching-engine)
7. [Material Weight & Cost Estimator](#material-weight--cost-estimator)
8. [Installation](#installation)
9. [Environment Setup](#environment-setup)
10. [CLI Reference](#cli-reference)
11. [GUI Reference](#gui-reference)
12. [Project Structure](#project-structure)
13. [Module-by-Module Breakdown](#module-by-module-breakdown)
14. [Testing](#testing)
15. [Extending the Project](#extending-the-project)
16. [Troubleshooting](#troubleshooting)
17. [Tech Stack](#tech-stack)
18. [License](#license)

---

## Overview

**API 6A** is the international standard governing wellhead and christmas tree equipment used in oil & gas drilling. This project automates the design of API 6A components by:

1. Accepting a **natural language prompt** (e.g., _"Generate API 6A bonnet 3-1/16 10k PSI"_).
2. Using a **multi-provider AI parsing pipeline** (Groq cloud LLM → local Ollama → regex fallback) to extract the part type, size (inches), and pressure rating (PSI).
3. Looking up a **136-row CSV dataset** for the exact engineering dimensions (flange OD, bore, bolt count, etc.).
4. If no exact match exists, the **fuzzy matching engine** suggests the 3 closest available configurations.
5. Building a **parametric 3D solid** using CadQuery with full dimensional validation.
6. Exporting the model as a **STEP file** (ISO 10303) into the `output/` directory.
7. Optionally computing the **weight (kg)** and **estimated raw material cost (INR)** for 9 engineering alloys.

All of this is accessible through both a **command-line interface** and a **dark-themed Tkinter GUI** with interactive parametric sliders.

---

## Architecture & Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                   │
│   "Generate API 6A bonnet 3-1/16 10k PSI"                          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│               AI PARSING PIPELINE (extract_request)                 │
│                                                                     │
│   1. parse_part() ──► detects: bonnet/flange/spool/blind/tee/gasket│
│   2. _try_groq()  ──► Groq cloud (llama-3.1-8b-instant)           │
│   3. _try_ollama() ─► Local Ollama (llama3)                        │
│   4. Regex fallback ► _fraction_to_decimal() + _parse_pressure()   │
│   5. normalize_to_sixteenth() ──► snaps to nearest 1/16"           │
│                                                                     │
│   Output: (part="bonnet", size=3.0625, pressure=10000)             │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│               DATASET LOOKUP (load_dimensions)                      │
│                                                                     │
│   Reads data/api6a.csv → filters by (part, size, pressure)         │
│   If no exact match → find_closest_match() suggests top 3          │
│                                                                     │
│   Output: dict with 22 dimension keys (body_od, bore, etc.)        │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│           (Optional) PARAMETRIC EDITING (GUI only)                  │
│                                                                     │
│   User adjusts dimensions via sliders/spinboxes before generation  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│               3D MODEL GENERATION (build_model)                     │
│                                                                     │
│   Routes to correct CadQuery builder:                               │
│     bonnet → model/bonnet.py  (build_bonnet_api_style)             │
│     flange → model/flange.py  (build_flange)                       │
│     spool  → model/spool.py   (build_spool)                        │
│     blind  → model/blind.py   (build_blind_flange)                 │
│     tee    → model/tee.py     (build_tee)                          │
│     gasket → model/gasket.py  (build_ring_gasket)                  │
│                                                                     │
│   Output: cq.Workplane (3D solid)                                  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│               EXPORT & ESTIMATION                                   │
│                                                                     │
│   export_step() → output/bonnet_3_0625_10000_20260502_101530.step  │
│   calculate_weight_cost() → Weight: 2.45 kg | Cost: ₹245.00 INR      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Supported Part Types

### 1. Bonnet (`model/bonnet.py`)
A multi-section cylindrical component used as a pressure-containing cap on gate valves.

**Geometry:** Three stacked cylinders (flange → hub → body) with a through-bore, bolt holes in the flange, an optional counterbore near the top, and an optional annular seal groove.

**Parameters (16):**
`body_od`, `body_height`, `bore`, `flange_od`, `flange_thk`, `hub_od`, `hub_height`, `bolt_circle_dia`, `bolt_hole_dia`, `bolt_count`, `fillet_r`, `counterbore_dia`, `counterbore_depth`, `seal_groove_dia`, `seal_groove_width`, `seal_groove_depth`

### 2. Flange (`model/flange.py`)
A flat circular disk with a center bore and bolt holes, used to connect pipes and valves.

**Geometry:** Single cylinder with a through-bore and evenly-spaced bolt holes on a polar array.

**Parameters (7):**
`flange_od`, `flange_thk`, `bore`, `bolt_circle_dia`, `bolt_hole_dia`, `bolt_count`, `fillet_r`

### 3. Spool (`model/spool.py`)
A straight pipe section with a flange on each end.

**Geometry:** Two flanges (reusing `build_flange`) connected by a hollow pipe. A safety bore cut ensures the passage is clear end-to-end.

**Parameters (8):**
`flange_od`, `flange_thk`, `bore`, `bolt_circle_dia`, `bolt_hole_dia`, `bolt_count`, `spool_length`, `fillet_r`

### 4. Blind Flange (`model/blind.py`)
A solid disk used to seal off a pipe end — identical to a flange but with **no through-bore**.

**Geometry:** Solid cylinder with bolt holes and an optional face seal groove.

**Parameters (9):**
`flange_od`, `flange_thk`, `bolt_circle_dia`, `bolt_hole_dia`, `bolt_count`, `fillet_r`, `seal_groove_dia`, `seal_groove_width`, `seal_groove_depth`

### 5. Tee (`model/tee.py`)
A three-way pipe fitting with a main run and a 90° branch.

**Geometry:** Main run spool (two end flanges + pipe) with a perpendicular branch pipe and a third flange. All bores are cut through for full flow.

**Parameters (9):**
`flange_od`, `flange_thk`, `bore`, `bolt_circle_dia`, `bolt_hole_dia`, `bolt_count`, `spool_length`, `branch_length`, `fillet_r`

### 6. Ring Joint Gasket (`model/gasket.py`)
A metallic sealing ring that sits in the groove between two flanges.

**Geometry:** An octagonal cross-section profile (4 chamfered corners) revolved 360° around the Z axis to form a ring. Also supports an oval (rectangular) cross-section.

**Parameters (4):**
`gasket_od`, `gasket_id`, `gasket_height`, `octagonal` (True/False)

---

## Dataset Reference

**File:** `data/api6a.csv`

The master dataset contains **136 rows** across 6 part families. Each row is a unique (part, size, pressure) configuration with all the engineering dimensions needed by the CadQuery builders.

### Column Definitions

| Column | Unit | Description |
|---|---|---|
| `part` | — | Part type: `bonnet`, `flange`, `spool`, `blind`, `tee`, `gasket` |
| `size` | inches | Nominal bore size (e.g., 2.0625 = 2-1/16") |
| `pressure` | PSI | Pressure rating: 2000, 3000, 5000, 10000, 15000, or 20000 |
| `body_od` | mm | Outer diameter of the bonnet body cylinder |
| `body_height` | mm | Height of the bonnet body cylinder |
| `bore` | mm | Through-bore diameter |
| `flange_od` | mm | Outer diameter of the flange |
| `flange_thk` | mm | Flange thickness |
| `hub_od` | mm | Hub outer diameter (bonnet only) |
| `hub_height` | mm | Hub height (bonnet only) |
| `bolt_circle_dia` | mm | Bolt circle diameter |
| `bolt_hole_dia` | mm | Individual bolt hole diameter |
| `bolt_count` | — | Number of bolt holes |
| `fillet_r` | mm | Edge fillet radius |
| `counterbore_dia` | mm | Counterbore diameter (bonnet only) |
| `counterbore_depth` | mm | Counterbore depth (bonnet only) |
| `seal_groove_dia` | mm | Seal groove pitch diameter |
| `seal_groove_width` | mm | Seal groove width |
| `seal_groove_depth` | mm | Seal groove depth |
| `spool_length` | mm | Overall spool/tee length |
| `branch_length` | mm | Tee branch length |
| `gasket_od` | mm | Ring gasket outer diameter |
| `gasket_id` | mm | Ring gasket inner diameter |
| `gasket_height` | mm | Ring gasket height |

### Coverage Summary

| Part Type | Sizes | Pressures | Configurations |
|---|---|---|---|
| Bonnet | 1-13/16" to 7-1/16" (8 sizes) | 2000–20000 PSI | 47 |
| Flange | 1-13/16" to 7-1/16" (7 sizes) | 2000–15000 PSI | 22 |
| Spool | 1-13/16" to 5-1/8" (6 sizes) | 2000–15000 PSI | 23 |
| Blind Flange | 1-13/16" to 7-1/16" (7 sizes) | 2000–10000 PSI | 17 |
| Tee | 2-1/16" to 5-1/8" (4 sizes) | 5000–15000 PSI | 10 |
| Ring Gasket | 1-13/16" to 7-1/16" (6 sizes) | 2000–10000 PSI | 17 |
| **Total** | | | **136** |

---

## AI Parsing Pipeline

The function `extract_request(user_text)` extracts `(part, size_inch, pressure_psi)` from free-text input. It tries three providers in order:

### Provider 1: Groq Cloud LLM
- **Model:** `llama-3.1-8b-instant`
- **Trigger:** `GROQ_API_KEY` is set in `.env`
- **How it works:** Sends a system prompt instructing the LLM to return JSON `{"size_inch": float, "pressure_psi": int}`. Temperature is set to 0 for deterministic output.
- **Latency:** ~200–500ms

### Provider 2: Local Ollama
- **Model:** `llama3`
- **Trigger:** `ollama` Python package is installed and the Ollama daemon is running locally
- **How it works:** Same JSON extraction prompt as Groq, but runs against a local model
- **Latency:** ~1–5s depending on hardware

### Provider 3: Regex Fallback
- **Trigger:** Always available (no dependencies)
- **How it works:**
  - `_fraction_to_decimal()` — matches patterns like `3-1/16`, `3 1/16`, or `3.0625`
  - `_parse_pressure()` — matches `10k`, `10,000`, or `10000`
  - `parse_part()` — keyword detection for `bonnet`, `flange`, `spool`, `blind`, `tee`, `gasket`/`ring`
- **Latency:** <1ms

### Size Normalization
After parsing, `normalize_to_sixteenth(size)` snaps the result to the nearest 1/16" increment to prevent float mismatch with the dataset (e.g., `3.06` → `3.0625`).

---

## Fuzzy Matching Engine

When `load_dimensions()` finds no exact match, `find_closest_match()` returns the **top 3** most similar configurations from the dataset.

**Algorithm:**
```
distance = |size_dataset − size_requested| + 0.5 × |pressure_dataset − pressure_requested| / max_pressure
```

- Size difference is weighted at 1.0 (dominant factor)
- Pressure difference is normalized by the maximum pressure in the dataset and weighted at 0.5
- Results are sorted ascending by distance

**Behavior:**
- **CLI:** Prints suggestions and asks _"Would you like to try the closest match? (y/n)"_
- **GUI:** Shows a dialog with 3 suggestions and a one-click accept button

---

## Material Weight & Cost Estimator

The function `calculate_weight_cost(model, material_name)` computes:
1. **Volume** — via `model.val().Volume()` (CadQuery returns mm³)
2. **Weight** — `volume_m³ × density_kg/m³`
3. **Cost** — `weight_kg × cost_per_kg_INR`

### Supported Materials

| Material | Density (kg/m³) | Cost (INR/kg) |
|---|---|---|
| Carbon Steel (A105) | 7,850 | ₹100.00 |
| Stainless Steel 316 | 8,000 | ₹375.00 |
| Stainless Steel 304 | 8,000 | ₹317.00 |
| Duplex Steel (2205) | 7,800 | ₹542.00 |
| Inconel 625 | 8,440 | ₹2087.00 |
| Inconel 718 | 8,190 | ₹2500.00 |
| Monel 400 | 8,800 | ₹1500.00 |
| Titanium Grade 5 | 4,430 | ₹2922.00 |
| Aluminum 6061 | 2,700 | ₹250.00 |

The GUI displays the result in the **Material & Weight Estimator** card immediately after STEP generation.

---

## Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/Generative-AI-Based-Automated-3D-CAD-Model-Generator.git
cd Generative-AI-Based-Automated-3D-CAD-Model-Generator-main
```

### Step 2: Create and Activate a Virtual Environment
```bash
# Create
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Linux / macOS)
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -m pytest tests/ -v
```
Expected output: `60 passed`.

---

## Environment Setup

### `.env` File
Copy the template and add your key:
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Get a free key at https://console.groq.com
GROQ_API_KEY=gsk_your_key_here
```

> **Note:** The Groq key is optional. Without it the system falls back to Ollama → Regex.

### `requirements.txt`
```
cadquery
pandas
ollama
ezdxf
tk
groq
python-dotenv
pytest
```

---

## CLI Reference

**Entry point:** `cli.py`

### Options

| Flag | Description |
|---|---|
| (no flags) | Interactive mode — prompts you to type a request |
| `--prompt "TEXT"` | One-shot mode — parses TEXT and generates a STEP file |
| `--list` | Lists all 136 supported (part, size, pressure) configurations |
| `-h` / `--help` | Shows the help message with examples |

### Examples

```bash
# List all configurations
python cli.py --list

# Generate a bonnet
python cli.py --prompt "Generate API 6A bonnet 3-1/16 10k PSI"

# Generate a flange
python cli.py --prompt "flange 2-1/16 5000"

# Generate a spool
python cli.py --prompt "spool 4-1/16 10k"

# Generate a blind flange
python cli.py --prompt "blind flange 3-1/16 10k"

# Generate a tee fitting
python cli.py --prompt "tee 3-1/16 10k"

# Generate a ring joint gasket
python cli.py --prompt "ring gasket 2-1/16 10k"

# Interactive mode
python cli.py
#   Enter prompt (bonnet / flange / spool): bonnet 2-1/16 10k
```

### Output
STEP files are saved to `output/` with a timestamped filename:
```
output/bonnet_3_0625_10000_20260502_101530.step
```

### Fuzzy Match (CLI)
If no exact match is found:
```
[ERROR] No exact match for part=bonnet, size=3.5", pressure=12000 PSI.

Closest available:
  - bonnet 3.5" @ 10000 PSI
  - bonnet 3.5" @ 15000 PSI
  - bonnet 3.0625" @ 10000 PSI

Would you like to try the closest match? (y/n): y
Using: bonnet 3.5" @ 10000 PSI
[SUCCESS] STEP created: D:\...\output\bonnet_3_5_10000_20260502_102000.step
```

---

## GUI Reference

**Launch:**
```bash
python ui/app.py
```

### Interface Sections

| Section | Description |
|---|---|
| **Header** | Title and pipeline overview |
| **Prompt Input** | Free-text entry with Enter-to-submit |
| **Quick Samples** | 6 buttons (Bonnet, Flange, Spool, Blind, Tee, Gasket) that auto-fill the prompt |
| **Material Dropdown** | Select from 9 engineering alloys |
| **Weight/Cost Display** | Shows Weight (kg), Volume (cm³), and Est. Cost (INR) after generation |
| **Parametric Sliders** | Scrollable panel of sliders and text entries for every dimension — edit before export |
| **Status / Output** | Log pane with progress bar and success/error messages |
| **Footer** | Supported parts and tips |

### Two-Step Workflow
1. **Click "1. Parse & Lookup"** — parses the prompt, loads dimensions from CSV, and populates the sliders
2. **Adjust sliders** (optional) — fine-tune any dimension before building the 3D model
3. **Click "2. Generate STEP"** — builds the CadQuery model, exports the STEP file, and displays weight/cost

### Dark Theme
The UI uses a curated color palette: `#1e1e2e` (background), `#89b4fa` (accent), `#a6e3a1` (success), `#f38ba8` (error).

---

## Project Structure

```
Generative-AI-Based-Automated-3D-CAD-Model-Generator-main/
│
├── .env.example          # Template for environment variables
├── .gitignore            # Git exclusions (.venv, .env, output/*.step, etc.)
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── cli.py                # Command-line interface entry point
├── main.py               # Core library (parsers, dataset, builders, estimator)
│
├── data/
│   ├── api6a.csv         # Master dataset (136 configurations, 24 columns)
│   └── batch_jobs.csv    # Example batch input file
│
├── model/
│   ├── __init__.py       # Package init
│   ├── bonnet.py         # Bonnet builder (build_bonnet_api_style)
│   ├── flange.py         # Flange builder (build_flange)
│   ├── spool.py          # Spool builder (build_spool)
│   ├── blind.py          # Blind flange builder (build_blind_flange)
│   ├── tee.py            # Tee fitting builder (build_tee)
│   └── gasket.py         # Ring gasket builder (build_ring_gasket)
│
├── drawing/
│   └── dxf_parser.py     # DXF text annotation parser (extracts KEY=VALUE dims)
│
├── ui/
│   └── app.py            # Tkinter GUI (dark theme, sliders, material estimator)
│
├── tests/
│   ├── __init__.py       # Package init
│   ├── test_parsers.py   # 19 tests: fractions, pressure, part detection, normalization
│   ├── test_dataset.py   # 16 tests: CSV integrity, columns, NaN, loading, all 6 parts
│   └── test_fuzzy.py     # 7 tests: distance calc, sorting, top-N, edge cases
│
└── output/               # Generated STEP files land here (auto-created)
    └── .gitkeep          # Ensures folder is tracked by Git
```

---

## Module-by-Module Breakdown

### `main.py` — Core Library (480 lines)

| Section | Functions | Purpose |
|---|---|---|
| **Material Database** | `MATERIALS` dict, `calculate_weight_cost()` | 9 alloys with density and cost; volume → weight → cost |
| **Fallback Parsers** | `_fraction_to_decimal()`, `_parse_pressure()`, `normalize_to_sixteenth()`, `parse_part()` | Regex-based extraction of size, pressure, and part type |
| **LLM Parsers** | `_try_groq()`, `_try_ollama()` | Cloud and local LLM JSON extraction |
| **Orchestrator** | `extract_request()` | Chains all 3 providers: Groq → Ollama → Regex |
| **Dataset** | `list_supported()`, `find_closest_match()`, `load_dimensions()` | CSV I/O, fuzzy matching, dimension loading |
| **Export** | `export_step()`, `unique_step_name()` | STEP file writing with timestamps |
| **Generator** | `build_model()`, `generate_from_prompt()`, `generate_from_dims()` | Routes to correct builder; two entry points (prompt-based and dimension-based) |

### `cli.py` — Command-Line Interface (82 lines)
Argparse wrapper with `--prompt`, `--list`, and interactive mode. Includes fuzzy match fallback with user confirmation.

### `ui/app.py` — Tkinter GUI (480 lines)
Dark-themed desktop app with: prompt entry, 6 quick-sample buttons, material dropdown, scrollable parametric sliders, progress bar, and log pane.

### `drawing/dxf_parser.py` — DXF Annotation Parser (70 lines)
Reads TEXT/MTEXT entities from a `.dxf` file, looking for `KEY=VALUE` or `KEY: VALUE` patterns. Maps uppercase keys (e.g., `BODY_OD`) to lowercase dict keys used by the builders. Useful for extracting dimensions from 2D engineering drawings.

---

## Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Test Breakdown

| File | Tests | What It Covers |
|---|---|---|
| `test_parsers.py` | 19 | Fraction conversion (12 cases), pressure parsing (10 cases), part detection for all 6 types, size normalization |
| `test_dataset.py` | 16 | CSV exists, loads, has all 24 columns, no NaN in critical fields, all 6 part types present, 100+ rows, valid pressures, dimension loading for every part type |
| `test_fuzzy.py` | 7 | Exact match returns distance 0, close sizes return suggestions, top-N limiting, wrong part type fallback, extreme values, sort order, same-part preference |
| **Total** | **60** | |

---

## Extending the Project

### Add a New Part Type

1. **Create** `model/newpart.py` with a function `build_newpart(**dims) -> cq.Workplane`
2. **Import** it in `main.py` and add an `elif part == "newpart"` branch in `build_model()`
3. **Update** `parse_part()` to detect the keyword
4. **Add rows** to `data/api6a.csv` with the correct `part` value and dimensions
5. **Add tests** in `tests/test_parsers.py` and `tests/test_dataset.py`
6. **Add a quick-sample button** in `ui/app.py`

### Add a New Material
Add an entry to the `MATERIALS` dict in `main.py`:
```python
"Hastelloy C276": {"density_kg_m3": 8890, "cost_per_kg_inr": 3340.00},
```

### Add a New Size/Pressure Combination
Append a row to `data/api6a.csv`. The system picks it up automatically — no code changes needed.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'cadquery'` | Run `pip install -r requirements.txt` inside your activated `.venv` |
| `UnicodeEncodeError` on Windows terminal | Fixed in this version — all emoji/special characters have been removed from print statements |
| Groq returns `None` | Check that `GROQ_API_KEY` is set correctly in `.env` (no quotes, no trailing spaces) |
| `No exact match` error | The fuzzy matcher will suggest alternatives. You can also run `python cli.py --list` to see all available configurations |
| GUI looks tiny on high-DPI display | The app calls `SetProcessDpiAwareness(1)` on Windows automatically |
| `_parse_pressure("10,000")` returns None | Fixed — commas are stripped before regex matching |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **3D CAD Engine** | [CadQuery](https://cadquery.readthedocs.io/) (parametric BREP modeling) |
| **Export Format** | STEP (ISO 10303-21) |
| **AI / LLM** | [Groq](https://groq.com/) cloud API (llama-3.1-8b-instant) |
| **Local LLM** | [Ollama](https://ollama.com/) (llama3) |
| **Data** | Pandas + CSV |
| **GUI** | Tkinter (dark theme, custom widgets) |
| **DXF Parsing** | [ezdxf](https://ezdxf.readthedocs.io/) |
| **Testing** | pytest |
| **Language** | Python 3.11+ |

---

## License

This project is licensed under the **MIT License** — see `LICENSE` for details.

---

_Built with CadQuery, Groq, and Python. Designed for engineers who think in inches and PSI._
