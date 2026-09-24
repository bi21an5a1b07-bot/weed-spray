"""Project one nadir pixel into local north/east. No MAVSDK and no camera FOV default.

Flat ground, camera straight down, vehicle level, square pixels. Image-right is
body-right (+east at heading 0, nose north). Image-down is aft (-north at
heading 0). That image-down sign is a convention for the function; a Gazebo
frame still has to confirm the mount before georeference is turned on.
"""

from __future__ import annotations

import math

# (north edge, south edge, east edge, west edge), metres from home.
FenceNESW = tuple[float, float, float, float]


def project_nadir(
    *,
    cx: float,
    cy: float,
    frame_w: int,
    frame_h: int,
    hfov_deg: float | None,
    height_m: float | None,
    north_m: float,
    east_m: float,
    heading_deg: float,
    fence: FenceNESW | None = None,
) -> tuple[float, float] | None:
    """Return ``(north_m, east_m)`` of a pixel, or ``None`` if it cannot be placed.

    Args:
        cx: Box center x as a fraction of the frame width (0-1).
        cy: Box center y as a fraction of the frame height (0-1).
        frame_w: Frame width in pixels.
        frame_h: Frame height in pixels.
        hfov_deg: Horizontal field of view in degrees. ``None`` or not in
            ``(0, 180)`` refuses. This function does not invent a lens.
        height_m: Camera height above the ground in metres. ``None`` or
            non-positive refuses. Not barometric altitude and not local z.
        north_m: Vehicle north of home, metres.
        east_m: Vehicle east of home, metres.
        heading_deg: Clockwise degrees from north.
        fence: Optional ``(north, south, east, west)`` edges. A point outside
            is ``None``. The edge itself is inside.

    Returns:
        Local metres ``(north, east)``, or ``None``.
    """
    if height_m is None or height_m <= 0:
        return None
    if hfov_deg is None or hfov_deg <= 0 or hfov_deg >= 180:
        return None
    if frame_w <= 0 or frame_h <= 0:
        return None
    if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0):
        return None

    fx = (frame_w / 2) / math.tan(math.radians(hfov_deg) / 2)
    right_m = height_m * ((cx - 0.5) * frame_w) / fx
    # Square pixels: fy == fx. Image-down is aft, so forward is the negation.
    forward_m = -height_m * ((cy - 0.5) * frame_h) / fx
    heading = math.radians(heading_deg)
    north = north_m + forward_m * math.cos(heading) - right_m * math.sin(heading)
    east = east_m + forward_m * math.sin(heading) + right_m * math.cos(heading)

    if fence is not None:
        north_max, south_min, east_max, west_min = fence
        if north > north_max or north < south_min or east > east_max or east < west_min:
            return None
    return (north, east)
