"""Local NED and scan-height lidar on telemetry. No live PX4."""

from types import SimpleNamespace

import pytest

from weed_spray.backend.models import Telemetry
from weed_spray.backend.vehicle import Vehicle, apply_distance_sample


def test_scan_height_sets_distance_scan_m_not_hover_trust():
    telem = Telemetry()
    apply_distance_sample(telem, 2.0, relative_alt_m=2.0)
    assert telem.distance_scan_m == pytest.approx(2.0)
    assert telem.distance_sensor_m is None
    assert telem.distance_sensor_missing is True


def test_hover_sample_sets_short_range_and_not_scan():
    telem = Telemetry()
    apply_distance_sample(telem, 0.27, relative_alt_m=0.27)
    assert telem.distance_sensor_m == pytest.approx(0.27)
    assert telem.distance_sensor_missing is False
    assert telem.distance_scan_m is None


def test_missing_or_non_positive_leaves_both_empty():
    telem = Telemetry()
    apply_distance_sample(telem, None, relative_alt_m=2.0)
    apply_distance_sample(telem, 0, relative_alt_m=2.0)
    apply_distance_sample(telem, float("nan"), relative_alt_m=2.0)
    assert telem.distance_sensor_m is None
    assert telem.distance_scan_m is None
    assert telem.north_m is None
    assert telem.east_m is None


@pytest.mark.parametrize("bad", [None, 0, float("nan")])
def test_missing_after_scan_clears_distance_scan_m(bad):
    """Once filled, a missing/non-positive sample must not leave sticky scan metres."""
    telem = Telemetry()
    apply_distance_sample(telem, 2.0, relative_alt_m=2.0)
    assert telem.distance_scan_m == pytest.approx(2.0)
    assert telem.distance_sensor_stream_alive is True
    apply_distance_sample(telem, bad, relative_alt_m=2.0)
    assert telem.distance_sensor_m is None
    assert telem.distance_scan_m is None
    assert telem.distance_sensor_stream_alive is False


@pytest.mark.asyncio
async def test_ned_tracker_stores_north_east_and_not_agl():
    vehicle = Vehicle()

    async def samples():
        yield SimpleNamespace(position=SimpleNamespace(north_m=3.0, east_m=-1.5, down_m=2.0))

    vehicle.drone = SimpleNamespace(telemetry=SimpleNamespace(position_velocity_ned=samples))
    await vehicle._track_local_ned()
    telem = vehicle.telemetry
    assert telem.north_m == pytest.approx(3.0)
    assert telem.east_m == pytest.approx(-1.5)
    assert telem.ned_down_m == pytest.approx(2.0)
    assert telem.distance_sensor_m is None
    assert telem.distance_scan_m is None
    assert telem.relative_alt_m is None
