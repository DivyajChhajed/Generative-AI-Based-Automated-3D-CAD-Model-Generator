import cadquery as cq


def build_bonnet_api_style(
    body_od: float,
    body_height: float,
    bore: float,
    flange_od: float,
    flange_thk: float,
    hub_od: float,
    hub_height: float,
    bolt_circle_dia: float,
    bolt_hole_dia: float,
    bolt_count: int,
    fillet_r: float = 0.0,
    # Optional features (set to 0 to disable)
    counterbore_dia: float = 0.0,
    counterbore_depth: float = 0.0,
    seal_groove_dia: float = 0.0,
    seal_groove_width: float = 0.0,
    seal_groove_depth: float = 0.0,
) -> cq.Workplane:
    """
    API-style bonnet-like model (parametric), units in mm:

    Base:
      - flange cylinder
      - hub (step) cylinder
      - body cylinder
      - through bore
      - bolt circle holes in flange
      - optional fillets

    Optional:
      - counterbore near top
      - seal groove (simple annular groove)
    """

    # -------- validation --------
    for name, v in [
        ("body_od", body_od),
        ("body_height", body_height),
        ("bore", bore),
        ("flange_od", flange_od),
        ("flange_thk", flange_thk),
        ("hub_od", hub_od),
        ("hub_height", hub_height),
        ("bolt_circle_dia", bolt_circle_dia),
        ("bolt_hole_dia", bolt_hole_dia),
    ]:
        if v <= 0:
            raise ValueError(f"{name} must be > 0")

    if bolt_count <= 0:
        raise ValueError("bolt_count must be > 0")

    if bore >= body_od:
        raise ValueError("bore must be smaller than body_od")

    if flange_od < body_od:
        raise ValueError("flange_od should be >= body_od")

    if hub_od < body_od:
        raise ValueError("hub_od should be >= body_od")

    if hub_od > flange_od:
        raise ValueError("hub_od should be <= flange_od")

    if bolt_circle_dia >= flange_od:
        raise ValueError("bolt_circle_dia must be smaller than flange_od")

    total_height = flange_thk + hub_height + body_height

    # -------- build solids (stacked) --------
    flange = cq.Workplane("XY").circle(flange_od / 2.0).extrude(flange_thk)

    hub = (
        cq.Workplane("XY")
        .workplane(offset=flange_thk)
        .circle(hub_od / 2.0)
        .extrude(hub_height)
    )

    body = (
        cq.Workplane("XY")
        .workplane(offset=flange_thk + hub_height)
        .circle(body_od / 2.0)
        .extrude(body_height)
    )

    bonnet = flange.union(hub).union(body)

    # -------- through bore --------
    bonnet = bonnet.faces(">Z").workplane().hole(bore, depth=total_height + 2)

    # -------- bolt holes (through flange only) --------
    # Get a workplane at top of flange:
    bolt_wp = bonnet.faces(">Z").workplane(offset=-(body_height + hub_height))
    bolt_wp = bolt_wp.polarArray(bolt_circle_dia / 2.0, 0, 360, bolt_count)
    bonnet = bolt_wp.hole(bolt_hole_dia, depth=flange_thk + 2)

    # -------- optional counterbore near top --------
    if counterbore_dia > 0 and counterbore_depth > 0:
        if counterbore_dia <= bore:
            raise ValueError("counterbore_dia must be > bore")
        if counterbore_depth >= body_height:
            raise ValueError("counterbore_depth must be < body_height")

        bonnet = (
            bonnet.faces(">Z")
            .workplane()
            .hole(counterbore_dia, depth=counterbore_depth)
        )

    # -------- optional seal groove (simple annular groove) --------
    # Implemented as: cut a ring pocket on a plane below top face.
    if seal_groove_dia > 0 and seal_groove_width > 0 and seal_groove_depth > 0:
        if seal_groove_dia >= body_od:
            raise ValueError("seal_groove_dia must be < body_od")
        if seal_groove_dia <= bore:
            raise ValueError("seal_groove_dia must be > bore")

        groove_outer_r = (seal_groove_dia / 2.0) + (seal_groove_width / 2.0)
        groove_inner_r = (seal_groove_dia / 2.0) - (seal_groove_width / 2.0)
        if groove_inner_r <= (bore / 2.0):
            raise ValueError("seal_groove_width too large; groove overlaps bore")

        # Cut groove on a plane a bit below top of hub/body
        bonnet = (
            bonnet.faces(">Z")
            .workplane(offset=-(seal_groove_depth))  # small offset
            .circle(groove_outer_r)
            .circle(groove_inner_r)
            .cutBlind(-seal_groove_depth)
        )

    # -------- optional fillets --------
    if fillet_r and fillet_r > 0:
        try:
            bonnet = bonnet.edges("|Z").fillet(fillet_r)
        except Exception:
            pass

    return bonnet
