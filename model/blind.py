import cadquery as cq


def build_blind_flange(
    flange_od: float,
    flange_thk: float,
    bolt_circle_dia: float,
    bolt_hole_dia: float,
    bolt_count: int,
    fillet_r: float = 0.0,
    seal_groove_dia: float = 0.0,
    seal_groove_width: float = 0.0,
    seal_groove_depth: float = 0.0,
) -> cq.Workplane:
    """
    Blind Flange (API 6A) — a solid disk with bolt holes but NO through-bore.

    Used to seal off the end of a pipe or valve connection.
    Units in mm.
    """
    if flange_od <= 0 or flange_thk <= 0:
        raise ValueError("flange_od and flange_thk must be > 0")
    if bolt_circle_dia >= flange_od:
        raise ValueError("bolt_circle_dia must be smaller than flange_od")
    if bolt_count <= 0:
        raise ValueError("bolt_count must be > 0")

    # Main solid disk
    blind = cq.Workplane("XY").circle(flange_od / 2).extrude(flange_thk)

    # Bolt holes (through the full thickness)
    bolt_wp = blind.faces(">Z").workplane()
    bolt_wp = bolt_wp.polarArray(bolt_circle_dia / 2, 0, 360, bolt_count)
    blind = bolt_wp.hole(bolt_hole_dia, depth=flange_thk + 1)

    # Optional seal groove on the face
    if seal_groove_dia > 0 and seal_groove_width > 0 and seal_groove_depth > 0:
        groove_outer_r = (seal_groove_dia / 2.0) + (seal_groove_width / 2.0)
        groove_inner_r = (seal_groove_dia / 2.0) - (seal_groove_width / 2.0)
        if groove_inner_r > 0:
            blind = (
                blind.faces(">Z")
                .workplane()
                .circle(groove_outer_r)
                .circle(groove_inner_r)
                .cutBlind(-seal_groove_depth)
            )

    # Optional fillet
    if fillet_r and fillet_r > 0:
        try:
            blind = blind.edges("|Z").fillet(fillet_r)
        except Exception:
            pass

    return blind
