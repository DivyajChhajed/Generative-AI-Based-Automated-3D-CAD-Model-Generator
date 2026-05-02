# Generative AI‑Based API 6A CAD Model Generator

![Demo Screenshot](https://via.placeholder.com/800x400?text=API+6A+CAD+Generator+Demo)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Dataset](#dataset)
- [Command‑Line Interface (CLI)](#cli)
- [Graphical User Interface (GUI)](#gui)
- [Material & Cost Estimator](#material-cost-estimator)
- [Adding New Parts / Extending the Dataset](#adding‑new‑parts)
- [Testing](#testing)
- [Project Structure](#project‑structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project is a **generative AI‑powered CAD model generator** for **API 6A** oil‑&‑gas components (bonnets, flanges, spools, blind flanges, tees, and ring‑joint gaskets).  It parses natural‑language prompts, looks up a CSV data‑bank for the nearest matching dimensions, builds the 3‑D geometry with **CadQuery**, and exports a **STEP** file ready for downstream CAE/PLM tools.

The system now supports:
- **Cloud LLM parsing** via **Groq** (fast, reliable) with a local **Ollama** fallback and a deterministic regex fallback.
- **Fuzzy matching** to suggest the closest available configuration when an exact size/pressure does not exist.
- **Material selection** (9 engineering alloys) and an on‑the‑fly **weight‑and‑cost estimator**.
- **Interactive Tkinter UI** with dark‑mode styling, parametric sliders, quick‑sample buttons for all part types, and real‑time weight display.
- **Extensible CSV dataset** (now >130 rows covering six part families).

---

## Features

| Category | Details |
|---|---|
| **Parsing** | Groq (cloud) → Ollama (local) → Regex fallback. Handles fractions (`3‑1/16`), commas (`10,000`), `k` suffixes (`10k`). |
| **Fuzzy Matching** | `find_closest_match()` returns the top‑3 closest configurations, sorted by a weighted distance (size + normalized pressure). |
| **New Parts** | Blind flanges, tees, ring‑joint gaskets – each with dedicated CadQuery builders (`model/blind.py`, `model/tee.py`, `model/gasket.py`). |
| **Dataset** | `data/api6a.csv` now has columns `branch_length`, `gasket_od`, `gasket_id`, `gasket_height`. |
| **Material Estimator** | Nine materials (Carbon Steel, Stainless 316, Inconel 625, etc.) – density and unit cost. After generation the UI shows *Weight (kg)*, *Volume (cm³)*, and *Estimated cost (USD)*. |
| **UI** | Dark theme, responsive layout, scrollable parametric sliders, quick‑sample row, progress bar, status pane. |
| **CLI** | Simple commands: `--list`, `--prompt`, interactive mode, `--material` option to pre‑select material for the estimator. |
| **Testing** | 60 unit tests (parsers, dataset integrity, fuzzy matching, new parts). |

---

## Prerequisites

- **Python 3.11+** (tested on Windows 10/11).  
- **Git** (to clone the repo).  
- **Virtual environment** (recommended).  
- **Groq API key** (optional; stored in `.env` as `GROQ_API_KEY`).  
- **Optional:** `ollama` installed locally with the `llama3` model for offline parsing.

---

## Installation

```bash
# 1️⃣ Clone the repository
git clone https://github.com/your‑username/Generative-AI-Based-Automated-3D-CAD-Model-Generator.git
cd Generative-AI-Based-Automated-3D-CAD-Model-Generator-main

# 2️⃣ Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# (or `source .venv/bin/activate` on *nix)

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ (Optional) Create a .env file for Groq
#   Add your Groq API key – the UI and CLI will automatically pick it up.
#   Example .env content:
#   GROQ_API_KEY=your_groq_api_key_here

# 5️⃣ Verify the installation by running the test suite
python -m pytest tests/ -v
```
All tests should pass (`60 passed`).

---

## Dataset

The master CSV lives at **`data/api6a.csv`**.  Each row represents a concrete configuration:

```csv
part,size,pressure,body_od,body_height,bore,flange_od,flange_thk,hub_od,hub_height,bolt_circle_dia,bolt_hole_dia,bolt_count,fillet_r,counterbore_dia,counterbore_depth,seal_groove_dia,seal_groove_width,seal_groove_depth,spool_length,branch_length,gasket_od,gasket_id,gasket_height
```
- New columns (`branch_length`, `gasket_od`, `gasket_id`, `gasket_height`) are used by the tee and gasket builders.
- **Adding more rows**: just append a new CSV line with the appropriate values.  The CLI will automatically pick them up.

---

## Command‑Line Interface (CLI)

The entry‑point is **`cli.py`**.

### General usage
```bash
python cli.py [OPTIONS]
```

### Options
| Flag | Description |
|---|---|
| `--list` | Lists **all supported configurations** (part, size, pressure). |
| `--prompt "TEXT"` | One‑shot generation – parses `TEXT` and creates a STEP file. Example: `python cli.py --prompt "Generate API 6A blind flange 3‑1/16 10k"`. |
| `--material "NAME"` | Pre‑select a material for the weight‑cost estimator (defaults to *Carbon Steel (A105)*). Valid names are the keys of the `MATERIALS` dict. |
| `--interactive` *(default)* | Starts a small REPL prompting the user for a prompt. Press **Enter** to submit. |
| `-h`, `--help` | Show help message. |

### Examples
```bash
# List everything
python cli.py --list

# Generate a bonnet (interactive)
python cli.py
#   > Enter prompt: Generate API 6A bonnet 2-1/16 10k PSI

# One‑shot generation for a tee
python cli.py --prompt "tee 4-1/16 5k" --material "Stainless Steel 316"
```
The generated STEP file is placed in the project root with a timestamped name, e.g. `tee_4.0625_5000_20260502_101530.step`.

---

## Graphical User Interface (GUI)

Launch the UI with:
```bash
python ui/app.py
```
### UI Layout
1. **Header** – title & subtitle.
2. **Prompt Input** – free‑text box with *Quick Samples* for every part type.
3. **Material & Weight Estimator** – select a material (drop‑down) and see weight/volume/cost after generation.
4. **Parametric Dimensions** – scrollable sliders (or spin‑boxes) for every dimension that can be tweaked before exporting.
5. **Status / Output** – log pane, progress bar, and final success message.
6. **Footer** – tip about dataset extension.

### Quick Sample Buttons
| Button | Prompt inserted |
|---|---|
| **Bonnet** | `Generate API 6A bonnet 3-1/16 10k PSI` |
| **Flange** | `flange 4-1/16 5000` |
| **Spool** | `spool 2-1/16 15000` |
| **Blind** | `blind flange 3-1/16 10k` |
| **Tee** | `tee 3-1/16 10k` |
| **Gasket** | `ring gasket 2-1/16 10k` |

### Material Dropdown
Select one of the following (shown exactly as in the code):
- Carbon Steel (A105)
- Stainless Steel 316
- Stainless Steel 304
- Duplex Steel (2205)
- Inconel 625
- Inconel 718
- Monel 400
- Titanium Grade 5
- Aluminum 6061

After clicking **"2. Generate STEP"**, the UI:
- Builds the CadQuery model using the (potentially edited) dimensions.
- Exports a timestamped STEP file.
- Calculates weight & cost using the selected material and displays them.

---

## Material & Cost Estimator

Implemented in `main.py` as `calculate_weight_cost(model, material_name)`.  The function:
1. Retrieves density (kg/m³) and cost per kg (USD) from the `MATERIALS` dict.
2. Calls `model.val().Volume()` (mm³) → converts to m³ and cm³.
3. Computes `weight = volume_m³ * density`.
4. Returns a dict with **volume_mm³**, **volume_cm³**, **weight_kg**, **cost_usd**, and material metadata.

The UI shows the result in the *Material & Weight Estimator* card.  The CLI can also expose it via a `--material` flag (future enhancement).  The calculation is instantaneous and does **not** modify the STEP file.

---

## Adding New Parts / Extending the Dataset

### 1️⃣ Add a new builder
1. Create a module under `model/` (e.g., `model/custom_part.py`).
2. Implement a function `build_custom_part(**kwargs) -> cadquery.Workplane`.
3. Follow the existing pattern: validate arguments, build geometry, return the workplane.

### 2️⃣ Register the builder
- Import the function in `main.py`.
- Extend `parse_part()` to recognise the new keyword.
- Extend `build_model()` with a new `elif part == "custom"` branch.
- Add any extra CSV columns needed.

### 3️⃣ Update the CSV
- Add new rows with the correct `part` identifier.
- Include any extra columns (e.g., `custom_param`).
- Remember to keep the header line up‑to‑date.

### 4️⃣ Add tests
- Add unit tests in `tests/test_parsers.py` for detection.
- Add a dataset test in `tests/test_dataset.py` to verify loading works.
- Run the full suite again.

---

## Testing

The project ships with a comprehensive pytest suite.
```bash
python -m pytest tests/ -v
```
- **Parser tests** (`test_parsers.py`): fraction conversion, pressure parsing, part detection (including blind, tee, gasket).
- **Dataset tests** (`test_dataset.py`): CSV existence, column validation, NaN checks, presence of all six part types, minimum row count, pressure validation, and dimension‑loading for every part.
- **Fuzzy‑match tests** (`test_fuzzy.py`): distance calculations, ordering, top‑N results.

All 60 tests currently pass.

---

## Project Structure
```
Generative-AI-Based-Automated-3D-CAD-Model-Generator-main/
├─ .env                # optional Groq API key
├─ .venv/             # virtual environment (ignore in VCS)
├─ data/
│   └─ api6a.csv      # master dataset
├─ model/
│   ├─ bonnet.py      # existing builder
│   ├─ flange.py      # existing builder
│   ├─ spool.py       # existing builder
│   ├─ blind.py       # blind‑flange builder
│   ├─ tee.py         # tee builder
│   └─ gasket.py      # ring‑joint gasket builder
├─ output/            # ⬅ all generated STEP files land here (auto‑created)
│   └─ bonnet_3.0625_10000_20260502_101530.step
├─ tests/
│   ├─ test_parsers.py
│   ├─ test_dataset.py
│   └─ test_fuzzy.py
├─ ui/
│   └─ app.py          # Tkinter UI with material estimator
├─ main.py            # Core library (parsers, builders, weight estimator)
├─ cli.py              # CLI wrapper
├─ requirements.txt    # python dependencies
├─ README.md           # this file
└─ walkthrough.md      # summary of changes (auto‑generated)
```

---

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome‑part`).
3. Follow the **coding style** used in existing modules (type hints, docstrings).
4. Add or extend unit tests for any new functionality.
5. Run the full test suite locally.
6. Open a Pull Request with a clear description.

---

## License

This project is licensed under the **MIT License** – see `LICENSE` for details.

---

*Happy coding! 🚀*
