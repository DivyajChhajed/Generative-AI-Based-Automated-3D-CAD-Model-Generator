import cadquery as cq
import math


def build_ring_gasket(
    gasket_od: float,
    gasket_id: float,
    gasket_height: float,
    octagonal: bool = True,
) -> cq.Workplane:
    """
    Ring Joint Gasket (API 6A) — a metallic sealing ring that sits
    between two flanges in the ring groove.

    Two styles:
      - Oval (octagonal=False): simple rectangular cross-section ring
      - Octagonal (octagonal=True): chamfered/angled cross-section for
        better sealing (industry standard for high pressure)

    Units in mm.
    """
    if gasket_od <= 0 or gasket_id <= 0 or gasket_height <= 0:
        raise ValueError("gasket_od, gasket_id, gasket_height must be > 0")
    if gasket_id >= gasket_od:
        raise ValueError("gasket_id must be smaller than gasket_od")

    ring_width = (gasket_od - gasket_id) / 2.0

    if octagonal:
        # Build octagonal cross-section profile (2D sketch, then revolve)
        # The octagonal shape is a rectangle with the four corners chamfered
        chamfer = min(ring_width * 0.25, gasket_height * 0.25)

        # Cross-section points (in XZ plane, at radius = mean radius)
        # We'll sketch in the XZ plane and revolve around Z
        inner_r = gasket_id / 2.0
        outer_r = gasket_od / 2.0

        # Build as a revolved cross-section
        gasket = (
            cq.Workplane("XZ")
            .moveTo(inner_r + chamfer, 0)
            .lineTo(outer_r - chamfer, 0)
            .lineTo(outer_r, chamfer)
            .lineTo(outer_r, gasket_height - chamfer)
            .lineTo(outer_r - chamfer, gasket_height)
            .lineTo(inner_r + chamfer, gasket_height)
            .lineTo(inner_r, gasket_height - chamfer)
            .lineTo(inner_r, chamfer)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )
    else:
        # Simple oval/rectangular cross-section ring
        gasket = (
            cq.Workplane("XY")
            .circle(gasket_od / 2)
            .circle(gasket_id / 2)
            .extrude(gasket_height)
        )

    return gasket
