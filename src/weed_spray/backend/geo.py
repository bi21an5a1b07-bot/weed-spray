"""Local NED (metres from home) ↔ WGS84 helpers for geofence upload."""

from math import cos, radians

from .models import FenceBox

# metres per degree latitude
_M_PER_DEG_LAT = 111_320.0


def ned_to_latlon(
    home_lat: float, home_lon: float, north_m: float, east_m: float
) -> tuple[float, float]:
    """Return ``(lat, lon)`` for a point ``north_m`` / ``east_m`` from home."""
    lat = home_lat + north_m / _M_PER_DEG_LAT
    lon = home_lon + east_m / (_M_PER_DEG_LAT * cos(radians(home_lat)))
    return lat, lon


def fence_corners_latlon(
    home_lat: float, home_lon: float, box: FenceBox
) -> list[tuple[float, float]]:
    """Four WGS84 corners of ``box``, clockwise from north-east."""
    return [
        ned_to_latlon(home_lat, home_lon, box.north_m, box.east_m),
        ned_to_latlon(home_lat, home_lon, box.south_m, box.east_m),
        ned_to_latlon(home_lat, home_lon, box.south_m, box.west_m),
        ned_to_latlon(home_lat, home_lon, box.north_m, box.west_m),
    ]


def lawnmower_waypoints(box: FenceBox, spacing_m: float) -> list[tuple[float, float]]:
    """Return ``(north_m, east_m)`` scan vertices inside ``box``.

    Rows run north-south, alternating direction. ``spacing_m <= 0`` becomes 4 m.
    Endpoints are inset 1 m from the north/south edges so the path stays inside.
    """
    if spacing_m <= 0:
        spacing_m = 4.0
    points: list[tuple[float, float]] = []
    y = box.west_m + spacing_m / 2
    going_north = True
    while y <= box.east_m:
        if going_north:
            points.append((box.south_m + 1.0, y))
            points.append((box.north_m - 1.0, y))
        else:
            points.append((box.north_m - 1.0, y))
            points.append((box.south_m + 1.0, y))
        going_north = not going_north
        y += spacing_m
    return points
