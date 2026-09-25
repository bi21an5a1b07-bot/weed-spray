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
        # Inclusive edges + float from tan(hfov/2): a hand-calc metre edge must
        # not trip strict >/< (e.g. east ≈ 0.20000000000000015 vs 0.2).
        eps = 1e-9
        if (
            north > north_max + eps
            or north < south_min - eps
            or east > east_max + eps
            or east < west_min - eps
        ):
            return None
    return (north, east)


def project_oblique(
    *,
    cx: float,
    cy: float,
    frame_w: int,
    frame_h: int,
    hfov_deg: float | None,
    tilt_deg: float | None,
    height_m: float | None,
    north_m: float,
    east_m: float,
    heading_deg: float,
    fence: FenceNESW | None = None,
) -> tuple[float, float] | None:
    """Project a pixel through a forward-and-down camera onto flat ground.

    ``tilt_deg`` is the depression of the optical axis below the horizon.
    90 is straight down and matches :func:`project_nadir`. 0 is horizontal
    and misses the ground. Image-right is body-right. Image-down pitches
    with the camera (aft when the camera is nadir).

    Args:
        cx: Box center x as a fraction of the frame width (0-1).
        cy: Box center y as a fraction of the frame height (0-1).
        frame_w: Frame width in pixels.
        frame_h: Frame height in pixels.
        hfov_deg: Horizontal field of view in degrees. ``None`` refuses.
        tilt_deg: Depression below the horizon in degrees. ``None`` refuses.
        height_m: Camera height above the ground in metres. Not baro, not local z.
        north_m: Vehicle north of home, metres.
        east_m: Vehicle east of home, metres.
        heading_deg: Clockwise degrees from north.
        fence: Optional ``(north, south, east, west)`` edges.

    Returns:
        Local metres ``(north, east)`` of the ground hit, or ``None``.
    """
    if height_m is None or height_m <= 0:
        return None
    if hfov_deg is None or hfov_deg <= 0 or hfov_deg >= 180:
        return None
    if tilt_deg is None or tilt_deg <= 0 or tilt_deg > 90:
        return None
    if frame_w <= 0 or frame_h <= 0:
        return None
    if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0):
        return None

    fx = (frame_w / 2) / math.tan(math.radians(hfov_deg) / 2)
    x_right = ((cx - 0.5) * frame_w) / fx
    y_down = ((cy - 0.5) * frame_h) / fx
    tilt = math.radians(tilt_deg)
    # Optical axis (0, 0, 1) depressed by tilt: forward=cos, down=sin.
    forward = math.cos(tilt) - y_down * math.sin(tilt)
    down = math.sin(tilt) + y_down * math.cos(tilt)
    if down <= 1e-9:
        return None
    scale = height_m / down
    forward_m = scale * forward
    right_m = scale * x_right
    heading = math.radians(heading_deg)
    north = north_m + forward_m * math.cos(heading) - right_m * math.sin(heading)
    east = east_m + forward_m * math.sin(heading) + right_m * math.cos(heading)

    if fence is not None:
        north_max, south_min, east_max, west_min = fence
        eps = 1e-9
        if (
            north > north_max + eps
            or north < south_min - eps
            or east > east_max + eps
            or east < west_min - eps
        ):
            return None
    return (north, east)


def arrival_time_s(
    *,
    north_m: float,
    east_m: float,
    plant_north_m: float,
    plant_east_m: float,
    vn_m_s: float | None,
    ve_m_s: float | None,
    min_closing_m_s: float = 0.2,
) -> float | None:
    """Seconds until the vehicle reaches the plant at the current horizontal speed.

    ``vn_m_s`` / ``ve_m_s`` are north and east velocity. Down velocity is not
    used. Stopped or receding flight returns ``None`` (the ground point is
    unchanged; do not invent a time). Already there returns ``0``.

    Args:
        north_m: Vehicle north, metres.
        east_m: Vehicle east, metres.
        plant_north_m: Ground point north, metres.
        plant_east_m: Ground point east, metres.
        vn_m_s: North velocity, metres per second.
        ve_m_s: East velocity, metres per second.
        min_closing_m_s: Closing speed at or below this is not an approach.

    Returns:
        Seconds, or ``None``.
    """
    dn = plant_north_m - north_m
    de = plant_east_m - east_m
    dist = math.hypot(dn, de)
    if dist <= 1e-6:
        return 0.0
    if vn_m_s is None or ve_m_s is None:
        return None
    closing = (vn_m_s * dn + ve_m_s * de) / dist
    if closing <= min_closing_m_s:
        return None
    return dist / closing
