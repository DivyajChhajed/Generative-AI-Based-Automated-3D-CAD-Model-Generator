import cadquery as cq


def build_flange(
    flange_od: float,
    flange_thk: float,
    bore: float,
    bolt_circle_dia: float,
    bolt_hole_dia: float,
    bolt_count: int,
    fillet_r: float = 0.0,
) -> cq.Workplane:
    if flange_od <= 0 or flange_thk <= 0 or bore <= 0:
        raise ValueError("flange_od, flange_thk, bore must be > 0")
    if bore >= flange_od:
        raise ValueError("bore must be smaller than flange_od")
    if bolt_circle_dia >= flange_od:
        raise ValueError("bolt_circle_dia must be smaller than flange_od")
    if bolt_count <= 0:
        raise ValueError("bolt_count must be > 0")

    flange = cq.Workplane("XY").circle(flange_od / 2).extrude(flange_thk)

    # Bore through
    flange = flange.faces(">Z").workplane().hole(bore, depth=flange_thk + 1)

    # Bolt holes
    bolt_wp = flange.faces(">Z").workplane()
    bolt_wp = bolt_wp.polarArray(bolt_circle_dia / 2, 0, 360, bolt_count)
    flange = bolt_wp.hole(bolt_hole_dia, depth=flange_thk + 1)

    # Optional fillet
    if fillet_r and fillet_r > 0:
        try:
            flange = flange.edges("|Z").fillet(fillet_r)
        except Exception:
            pass

    return flange
