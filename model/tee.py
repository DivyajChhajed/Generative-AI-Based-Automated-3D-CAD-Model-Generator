import cadquery as cq
from .flange import build_flange


def build_tee(
    flange_od: float,
    flange_thk: float,
    bore: float,
    bolt_circle_dia: float,
    bolt_hole_dia: float,
    bolt_count: int,
    spool_length: float,
    branch_length: float = 0.0,
    fillet_r: float = 0.0,
) -> cq.Workplane:
    """
    Tee fitting (API 6A) — main run pipe with flanges on both ends,
    and a 90-degree branch pipe with a third flange.

    Layout (top view):
        [Flange]====[Main Pipe]====[Flange]
                         |
                    [Branch Pipe]
                         |
                      [Flange]

    Units in mm.
    """
    if spool_length <= flange_thk * 2:
        raise ValueError("spool_length must be greater than 2*flange_thk")
    if branch_length <= 0:
        branch_length = spool_length / 2.0
    if bore <= 0:
        raise ValueError("bore must be > 0")

    # --- Build main run (same as spool) ---
    # Left flange
    left = build_flange(
        flange_od=flange_od,
        flange_thk=flange_thk,
        bore=bore,
        bolt_circle_dia=bolt_circle_dia,
        bolt_hole_dia=bolt_hole_dia,
        bolt_count=bolt_count,
        fillet_r=fillet_r,
    )

    # Right flange shifted along Z
    right = left.translate((0, 0, spool_length - flange_thk))

    # Main pipe between flanges
    pipe_od = max(bore + 20, bolt_circle_dia * 0.65)
    pipe_len = spool_length - 2 * flange_thk

    main_pipe = (
        cq.Workplane("XY")
        .workplane(offset=flange_thk)
        .circle(pipe_od / 2)
        .extrude(pipe_len)
        .faces(">Z")
        .hole(bore, depth=pipe_len + 1)
    )

    tee = left.union(main_pipe).union(right)

    # --- Build branch (perpendicular, along Y axis) ---
    # Branch exits from the middle of the main run
    mid_z = spool_length / 2.0

    # Branch pipe (cylinder along Y, starting from outer surface of main pipe)
    branch_pipe = (
        cq.Workplane("XZ")
        .workplane(offset=0)
        .transformed(offset=(0, mid_z, pipe_od / 2))
        .circle(pipe_od / 2)
        .extrude(branch_length - flange_thk)
    )

    # Branch bore
    branch_bore = (
        cq.Workplane("XZ")
        .workplane(offset=0)
        .transformed(offset=(0, mid_z, 0))
        .circle(bore / 2)
        .extrude(branch_length + pipe_od)
    )

    # Branch flange (built flat, then rotated and translated)
    branch_flange = build_flange(
        flange_od=flange_od,
        flange_thk=flange_thk,
        bore=bore,
        bolt_circle_dia=bolt_circle_dia,
        bolt_hole_dia=bolt_hole_dia,
        bolt_count=bolt_count,
        fillet_r=fillet_r,
    )

    # Rotate flange to face outward along Y, then position it
    branch_flange = (
        branch_flange
        .rotateAboutCenter((1, 0, 0), -90)
        .translate((0, pipe_od / 2 + branch_length - flange_thk, mid_z))
    )

    # Combine everything
    tee = tee.union(branch_pipe).union(branch_flange)

    # Cut the main bore through the entire run
    tee = tee.cut(branch_bore)

    # Ensure main bore passes through entire run
    main_bore = (
        cq.Workplane("XY")
        .circle(bore / 2)
        .extrude(spool_length + 5)
    )
    tee = tee.cut(main_bore)

    return tee
