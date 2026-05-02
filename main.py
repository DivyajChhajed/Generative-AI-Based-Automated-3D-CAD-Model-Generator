import json
import re
import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import cadquery as cq

# Optional Ollama (fallback parsing works without it)
try:
    import ollama
except ImportError:
    ollama = None

# Optional Groq cloud LLM
try:
    from groq import Groq
except ImportError:
    Groq = None

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from model.bonnet import build_bonnet_api_style
from model.flange import build_flange
from model.spool import build_spool
from model.blind import build_blind_flange
from model.tee import build_tee
from model.gasket import build_ring_gasket


DATA_PATH = Path("data/api6a.csv")
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)   # create output/ on first import if missing


# -------------------- MATERIAL DATABASE --------------------

MATERIALS = {
    "Carbon Steel (A105)": {"density_kg_m3": 7850, "cost_per_kg_inr": 100.0},
    "Stainless Steel 316": {"density_kg_m3": 8000, "cost_per_kg_inr": 375.0},
    "Stainless Steel 304": {"density_kg_m3": 8000, "cost_per_kg_inr": 317.0},
    "Duplex Steel (2205)": {"density_kg_m3": 7800, "cost_per_kg_inr": 542.0},
    "Inconel 625": {"density_kg_m3": 8440, "cost_per_kg_inr": 2087.0},
    "Inconel 718": {"density_kg_m3": 8190, "cost_per_kg_inr": 2500.0},
    "Monel 400": {"density_kg_m3": 8800, "cost_per_kg_inr": 1500.0},
    "Titanium Grade 5": {"density_kg_m3": 4430, "cost_per_kg_inr": 2922.0},
    "Aluminum 6061": {"density_kg_m3": 2700, "cost_per_kg_inr": 250.0},
}


def calculate_weight_cost(model: cq.Workplane, material_name: str) -> dict:
    """
    Calculate the weight and estimated raw material cost for a CadQuery model.
    CadQuery volumes are in mm^3, so we convert to m^3 for weight.

    Returns: {"volume_mm3": float, "volume_cm3": float, "weight_kg": float,
              "cost_inr": float, "material": str, "density": float}
    """
    mat = MATERIALS.get(material_name)
    if mat is None:
        raise ValueError(f"Unknown material: {material_name}. Available: {list(MATERIALS.keys())}")

    # CadQuery .val().Volume() returns volume in mm^3
    volume_mm3 = model.val().Volume()
    volume_m3 = volume_mm3 * 1e-9  # mm^3 -> m^3
    volume_cm3 = volume_mm3 * 1e-3  # mm^3 -> cm^3

    weight_kg = volume_m3 * mat["density_kg_m3"]
    cost_inr = weight_kg * mat["cost_per_kg_inr"]

    return {
        "volume_mm3": round(volume_mm3, 2),
        "volume_cm3": round(volume_cm3, 2),
        "weight_kg": round(weight_kg, 3),
        "cost_inr": round(cost_inr, 2),
        "material": material_name,
        "density_kg_m3": mat["density_kg_m3"],
        "cost_per_kg_inr": mat["cost_per_kg_inr"],
    }


# -------------------- FALLBACK PARSERS --------------------

def _fraction_to_decimal(text: str):
    """
    Converts:
      '3-1/16', '3 1/16' -> decimal inches
      '3.0625' -> decimal inches
    """
    t = text.lower().replace('"', "").strip()

    m = re.search(r"\b(\d+)\s*[- ]\s*(\d+)\s*/\s*(\d+)\b", t)
    if m:
        whole = int(m.group(1))
        num = int(m.group(2))
        den = int(m.group(3))
        if den == 0:
            return None
        return whole + (num / den)

    m2 = re.search(r"\b(\d+\.\d+)\b", t)
    if m2:
        return float(m2.group(1))

    return None


def _parse_pressure(text: str):
    """
    Converts:
      '10k' -> 10000
      '10,000' -> 10000
      '10000' -> 10000
    """
    t = text.lower().replace(",", "")

    mk = re.search(r"\b(\d+)\s*k\b", t)
    if mk:
        return int(mk.group(1)) * 1000

    mn = re.search(r"\b(\d{4,6})\b", t)
    if mn:
        return int(mn.group(1))

    return None


def normalize_to_sixteenth(size_inch: float) -> float:
    """Snap to nearest 1/16 inch to avoid float mismatch."""
    return round(size_inch * 16) / 16.0


def parse_part(text: str) -> str:
    """
    Detect part type from prompt.
    Supports: bonnet, flange, spool, blind, tee, gasket
    Default: bonnet
    """
    t = text.lower()
    if "blind" in t:
        return "blind"
    if "gasket" in t or "ring" in t:
        return "gasket"
    if "tee" in t:
        return "tee"
    if "flange" in t:
        return "flange"
    if "spool" in t:
        return "spool"
    if "bonnet" in t:
        return "bonnet"
    return "bonnet"


# -------------------- PARSER (GROQ + OLLAMA + FALLBACK) --------------------

def _try_groq(user_text: str) -> dict | None:
    """Try parsing via Groq cloud LLM. Returns dict or None."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or Groq is None:
        return None

    system_prompt = (
        "Return ONLY valid JSON, nothing else.\n"
        "Schema:\n"
        "{\n"
        '  "size_inch": number,\n'
        '  "pressure_psi": integer\n'
        "}\n"
        "Rules:\n"
        "- Convert 3-1/16 to 3.0625.\n"
        "- Convert 2-1/16 to 2.0625.\n"
        "- Convert 10k or 10,000 to 10000.\n"
        "- Do not add extra keys.\n"
    )

    try:
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text: {user_text}\nReturn JSON now."},
            ],
            temperature=0,
            max_tokens=100,
        )
        content = resp.choices[0].message.content.strip()
        m = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            return {"size_inch": float(data["size_inch"]), "pressure_psi": int(data["pressure_psi"])}
    except Exception:
        pass
    return None


def _try_ollama(user_text: str) -> dict | None:
    """Try parsing via local Ollama LLM. Returns dict or None."""
    if ollama is None:
        return None

    system_prompt = (
        "Return ONLY valid JSON, nothing else.\n"
        "Schema:\n"
        "{\n"
        '  "size_inch": number,\n'
        '  "pressure_psi": integer\n'
        "}\n"
        "Rules:\n"
        "- Convert 3-1/16 to 3.0625.\n"
        "- Convert 2-1/16 to 2.0625.\n"
        "- Convert 10k or 10,000 to 10000.\n"
        "- Do not add extra keys.\n"
    )

    try:
        resp = ollama.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text: {user_text}\nReturn JSON now."},
            ],
            options={"temperature": 0},
        )

        content = resp["message"]["content"].strip()
        m = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            return {"size_inch": float(data["size_inch"]), "pressure_psi": int(data["pressure_psi"])}
    except Exception:
        pass
    return None


def extract_request(user_text: str) -> tuple[str, float, int]:
    """
    Returns: (part, size_inch, pressure_psi)
    Tries providers in order: Groq -> Ollama -> Regex fallback
    """
    part = parse_part(user_text)

    # Try Groq first (cloud, fast)
    result = _try_groq(user_text)

    # Then try Ollama (local)
    if result is None:
        result = _try_ollama(user_text)

    # Finally, regex fallback
    if result is None:
        size = _fraction_to_decimal(user_text)
        pressure = _parse_pressure(user_text)

        if size is None or pressure is None:
            raise ValueError(
                "Could not parse input.\n"
                "Try: Generate API 6A bonnet 3-1/16 10k PSI\n"
                "Try: Generate API 6A flange 3.0625 10000\n"
                "Try: Generate API 6A spool 3-1/16 10k\n"
                "Try: Generate API 6A blind flange 2-1/16 5k\n"
                "Try: Generate API 6A tee 3-1/16 10k\n"
                "Try: Generate API 6A ring gasket 2-1/16 10k\n"
            )
        result = {"size_inch": size, "pressure_psi": pressure}

    size = normalize_to_sixteenth(result["size_inch"])
    return part, size, result["pressure_psi"]


# -------------------- DATASET --------------------

def list_supported():
    df = pd.read_csv(DATA_PATH)
    df["size"] = df["size"].astype(float)
    df["pressure"] = df["pressure"].astype(int)
    df["part"] = df["part"].astype(str)
    return df[["part", "size", "pressure"]].drop_duplicates().sort_values(["part", "pressure", "size"])


def find_closest_match(part: str, size_inch: float, pressure_psi: int, top_n: int = 3) -> list[dict]:
    """
    Find the closest (part, size, pressure) combos from the dataset.
    Returns a list of dicts: [{"part": ..., "size": ..., "pressure": ..., "distance": ...}, ...]
    Distance is a weighted score: size difference (in inches) + normalized pressure difference.
    """
    if not DATA_PATH.exists():
        return []

    df = pd.read_csv(DATA_PATH)
    df["size"] = df["size"].astype(float)
    df["pressure"] = df["pressure"].astype(int)
    df["part"] = df["part"].astype(str)

    # Filter to same part type
    candidates = df[df["part"] == part][["part", "size", "pressure"]].drop_duplicates()

    if candidates.empty:
        # If no rows for this part type, search all
        candidates = df[["part", "size", "pressure"]].drop_duplicates()

    # Compute weighted distance
    max_pressure = candidates["pressure"].max() if not candidates.empty else 1
    candidates = candidates.copy()
    candidates["distance"] = (
        abs(candidates["size"] - size_inch) +
        0.5 * abs(candidates["pressure"] - pressure_psi) / max(max_pressure, 1)
    )

    closest = candidates.nsmallest(top_n, "distance")
    return closest.to_dict("records")


def load_dimensions(part: str, size_inch: float, pressure_psi: int) -> dict:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA_PATH.resolve()}")

    df = pd.read_csv(DATA_PATH)
    df["size"] = df["size"].astype(float)
    df["pressure"] = df["pressure"].astype(int)
    df["part"] = df["part"].astype(str)

    match = df[(df["part"] == part) & (df["pressure"] == pressure_psi) & (df["size"] == size_inch)]
    if match.empty:
        suggestions = find_closest_match(part, size_inch, pressure_psi)
        suggestion_lines = []
        for s in suggestions:
            suggestion_lines.append(f"  - {s['part']} {s['size']}\" @ {s['pressure']} PSI")
        suggestion_text = "\n".join(suggestion_lines) if suggestion_lines else "  (none)"

        raise ValueError(
            f"No exact match for part={part}, size={size_inch}\", pressure={pressure_psi} PSI.\n\n"
            f"Closest available:\n{suggestion_text}"
        )

    row = match.iloc[0]

    def g(col, default=0.0):
        return float(row[col]) if col in row and pd.notna(row[col]) else float(default)

    dims = {
        "body_od": g("body_od"),
        "body_height": g("body_height"),
        "bore": g("bore"),
        "flange_od": g("flange_od"),
        "flange_thk": g("flange_thk"),
        "hub_od": g("hub_od"),
        "hub_height": g("hub_height"),
        "bolt_circle_dia": g("bolt_circle_dia"),
        "bolt_hole_dia": g("bolt_hole_dia"),
        "bolt_count": int(row["bolt_count"]) if "bolt_count" in row and pd.notna(row["bolt_count"]) else 0,
        "fillet_r": g("fillet_r", 0.0),
        "counterbore_dia": g("counterbore_dia", 0.0),
        "counterbore_depth": g("counterbore_depth", 0.0),
        "seal_groove_dia": g("seal_groove_dia", 0.0),
        "seal_groove_width": g("seal_groove_width", 0.0),
        "seal_groove_depth": g("seal_groove_depth", 0.0),
        "spool_length": g("spool_length", 0.0),
        "branch_length": g("branch_length", 0.0),
        "gasket_od": g("gasket_od", 0.0),
        "gasket_id": g("gasket_id", 0.0),
        "gasket_height": g("gasket_height", 0.0),
    }

    return dims


# -------------------- EXPORT --------------------

def export_step(model: cq.Workplane, out_path: Path) -> Path:
    out_path = out_path.resolve()
    cq.exporters.export(model, str(out_path))
    return out_path


def unique_step_name(part: str, size_inch: float, pressure_psi: int) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    size_txt = str(size_inch).replace(".", "_")
    return f"{part}_{size_txt}_{pressure_psi}_{ts}.step"


# -------------------- GENERATOR --------------------

def build_model(part: str, dims: dict) -> cq.Workplane:
    """Build a CadQuery 3D model for the given part type and dimensions."""
    if part == "bonnet":
        # Filter ONLY bonnet keys to avoid unexpected keyword errors
        bonnet_keys = [
            "body_od", "body_height", "bore", "flange_od", "flange_thk",
            "hub_od", "hub_height", "bolt_circle_dia", "bolt_hole_dia",
            "bolt_count", "fillet_r", "counterbore_dia", "counterbore_depth",
            "seal_groove_dia", "seal_groove_width", "seal_groove_depth",
        ]
        bonnet_dims = {k: dims[k] for k in bonnet_keys if k in dims}
        return build_bonnet_api_style(**bonnet_dims)

    elif part == "flange":
        return build_flange(
            flange_od=dims["flange_od"],
            flange_thk=dims["flange_thk"],
            bore=dims["bore"],
            bolt_circle_dia=dims["bolt_circle_dia"],
            bolt_hole_dia=dims["bolt_hole_dia"],
            bolt_count=dims["bolt_count"],
            fillet_r=dims["fillet_r"],
        )

    elif part == "spool":
        return build_spool(
            flange_od=dims["flange_od"],
            flange_thk=dims["flange_thk"],
            bore=dims["bore"],
            bolt_circle_dia=dims["bolt_circle_dia"],
            bolt_hole_dia=dims["bolt_hole_dia"],
            bolt_count=dims["bolt_count"],
            spool_length=dims["spool_length"],
            fillet_r=dims["fillet_r"],
        )

    elif part == "blind":
        return build_blind_flange(
            flange_od=dims["flange_od"],
            flange_thk=dims["flange_thk"],
            bolt_circle_dia=dims["bolt_circle_dia"],
            bolt_hole_dia=dims["bolt_hole_dia"],
            bolt_count=dims["bolt_count"],
            fillet_r=dims["fillet_r"],
            seal_groove_dia=dims.get("seal_groove_dia", 0.0),
            seal_groove_width=dims.get("seal_groove_width", 0.0),
            seal_groove_depth=dims.get("seal_groove_depth", 0.0),
        )

    elif part == "tee":
        return build_tee(
            flange_od=dims["flange_od"],
            flange_thk=dims["flange_thk"],
            bore=dims["bore"],
            bolt_circle_dia=dims["bolt_circle_dia"],
            bolt_hole_dia=dims["bolt_hole_dia"],
            bolt_count=dims["bolt_count"],
            spool_length=dims["spool_length"],
            branch_length=dims.get("branch_length", 0.0),
            fillet_r=dims["fillet_r"],
        )

    elif part == "gasket":
        return build_ring_gasket(
            gasket_od=dims["gasket_od"],
            gasket_id=dims["gasket_id"],
            gasket_height=dims["gasket_height"],
            octagonal=True,
        )

    else:
        raise ValueError(f"Unknown part type: {part}")


def generate_from_prompt(prompt: str) -> str:
    part, size_inch, pressure_psi = extract_request(prompt)
    dims = load_dimensions(part, size_inch, pressure_psi)
    model = build_model(part, dims)
    out_name = unique_step_name(part, size_inch, pressure_psi)
    out_path = export_step(model, OUT_DIR / out_name)
    return str(out_path)


def generate_from_dims(part: str, size_inch: float, pressure_psi: int, dims: dict) -> str:
    """Generate a STEP file from explicit dimensions (used by UI with parametric overrides)."""
    model = build_model(part, dims)
    out_name = unique_step_name(part, size_inch, pressure_psi)
    out_path = export_step(model, OUT_DIR / out_name)
    return str(out_path)
