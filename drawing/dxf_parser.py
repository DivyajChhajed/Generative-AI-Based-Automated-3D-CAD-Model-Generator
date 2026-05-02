import re
import ezdxf


KEY_MAP = {
    "BODY_OD": "body_od",
    "BODY_HEIGHT": "body_height",
    "BORE": "bore",
    "FLANGE_OD": "flange_od",
    "FLANGE_THK": "flange_thk",
    "HUB_OD": "hub_od",
    "HUB_HEIGHT": "hub_height",
    "BOLT_CIRCLE_DIA": "bolt_circle_dia",
    "BOLT_HOLE_DIA": "bolt_hole_dia",
    "BOLT_COUNT": "bolt_count",
    "FILLET_R": "fillet_r",
    "COUNTERBORE_DIA": "counterbore_dia",
    "COUNTERBORE_DEPTH": "counterbore_depth",
    "SEAL_GROOVE_DIA": "seal_groove_dia",
    "SEAL_GROOVE_WIDTH": "seal_groove_width",
    "SEAL_GROOVE_DEPTH": "seal_groove_depth",
}


def _parse_key_value(text: str):
    """
    Accepts formats like:
      BODY_OD=165
      BORE : 52
      BOLT_COUNT=8
    """
    text = text.strip().upper()
    m = re.match(r"([A-Z0-9_]+)\s*[:=]\s*([-+]?\d+(\.\d+)?)", text)
    if not m:
        return None, None
    return m.group(1), float(m.group(2))


def extract_params_from_dxf(dxf_path: str) -> dict:
    """
    Reads DXF and extracts parameters from TEXT/MTEXT entities
    written in KEY=VALUE format.

    Returns dict with keys matching CadQuery generator parameters.
    """
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    params = {}

    for e in msp:
        t = e.dxftype()

        if t == "TEXT":
            raw = e.dxf.text
        elif t == "MTEXT":
            raw = e.text
        else:
            continue

        key, val = _parse_key_value(raw)
        if key in KEY_MAP:
            out_key = KEY_MAP[key]
            if out_key == "bolt_count":
                params[out_key] = int(val)
            else:
                params[out_key] = float(val)

    return params
