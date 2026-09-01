"""NED ↔ WGS84 helpers and lawnmower waypoint generation."""

import pytest

from weed_spray.backend.geo import fence_corners_latlon, lawnmower_waypoints, ned_to_latlon
from weed_spray.backend.models import FenceBox


def test_ned_north_increases_latitude():
    lat, lon = ned_to_latlon(40.0, -105.0, 111.32, 0.0)
    assert lat == pytest.approx(40.001, abs=1e-5)
    assert lon == pytest.approx(-105.0, abs=1e-9)


def test_ned_east_increases_longitude():
    _, lon0 = ned_to_latlon(40.0, -105.0, 0.0, 0.0)
    _, lon1 = ned_to_latlon(40.0, -105.0, 0.0, 100.0)
    assert lon1 > lon0


def test_fence_has_four_corners_clockwise_from_ne():
    box = FenceBox(north_m=20, south_m=-5, east_m=15, west_m=-15)
    corners = fence_corners_latlon(40.0, -105.0, box)
    assert len(corners) == 4
    lats = [c[0] for c in corners]
    lons = [c[1] for c in corners]
    assert lats[0] == lats[3]
    assert lats[1] == lats[2]
    assert lons[0] == lons[1]
    assert lons[2] == lons[3]
    assert lats[0] > lats[1]
    assert lons[0] > lons[3]


def test_lawnmower_covers_box_and_stays_inside():
    box = FenceBox(north_m=20, south_m=-5, east_m=15, west_m=-15)
    pts = lawnmower_waypoints(box, 5.0)
    assert pts
    for north, east in pts:
        assert box.south_m <= north <= box.north_m
        assert box.west_m <= east <= box.east_m


def test_lawnmower_zero_spacing_defaults():
    box = FenceBox()
    assert lawnmower_waypoints(box, 0) == lawnmower_waypoints(box, 4.0)
