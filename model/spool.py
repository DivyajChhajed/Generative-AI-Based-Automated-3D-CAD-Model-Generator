import cadquery as cq
from .flange import build_flange


def build_spool(
    flange_od: float,
    flange_thk: float,
    bore: float,
    bolt_circle_dia: float,
    bolt_hole_dia: float,
    bolt_count: int,
    spool_length: float,
    fillet_r: float = 0.0,
) -> cq.Workplane:
    if spool_length <= flange_thk * 2:
        raise ValueError("spool_length must be greater than 2*flange_thk")

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

    # Right flange shifted
    right = left.translate((0, 0, spool_length - flange_thk))

    # Pipe between flanges (outer diameter chosen as bolt circle * 0.65 for demo)
    pipe_od = max(bore + 20, bolt_circle_dia * 0.65)
    pipe_len = spool_length - 2 * flange_thk

    pipe = (
        cq.Workplane("XY")
        .workplane(offset=flange_thk)
        .circle(pipe_od / 2)
        .extrude(pipe_len)
        .faces(">Z")
        .hole(bore, depth=pipe_len + 1)
    )

    spool = left.union(pipe).union(right)

    # Ensure bore passes through entire part (safety cut)
    spool = spool.faces(">Z").workplane().hole(bore, depth=spool_length + 5)

    return spool
