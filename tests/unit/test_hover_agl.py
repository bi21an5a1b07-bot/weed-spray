"""Offboard AGL hover seam (issue #19) — FakeVehicle only; no live PX4."""

import pytest

from tests.fakes import FakeVehicle
from weed_spray.backend.config import Settings
from weed_spray.backend.mission import Mission
from weed_spray.backend.models import ConfirmDecision, Detection


@pytest.mark.asyncio
async def test_goto_global_agl_records_lat_lon_agl():
    v = FakeVehicle()
    await v.goto_global_agl(40.1, -105.2, 0.22, settle_s=0.0)
    assert v.goto_agls == [(40.1, -105.2, 0.22)]


@pytest.mark.asyncio
async def test_visit_uses_offboard_agl_when_configured(monkeypatch):
    """Gazebo candidate: XY at scan NED, then PositionGlobalYaw AGL hover."""
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        Settings(hover_altitude_mode="offboard_agl", hover_agl_m=0.22, scan_agl_m=2.0),
    )
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    v._telem.distance_sensor_missing = False
    v._telem.distance_sensor_m = 0.22
    m = Mission(v)
    m.state.detections = [
        Detection(id="w1", class_name="dandelion", north_m=1.0, east_m=2.0, conf=0.9)
    ]
    m.state.confirms = [ConfirmDecision(detection_id="w1", decision="confirm")]
    await m._visit_confirmed()
    # last goto should be AGL hover, not NED down=-0.22
    assert v.goto_agls
    assert v.goto_agls[-1] == (40.01, -105.01, 0.22)
    assert m.state.hover_agl_m[0].missing is False
    assert m.state.hover_agl_m[0].agl_m == pytest.approx(0.22)


@pytest.mark.asyncio
async def test_visit_default_ned_does_not_call_agl(monkeypatch):
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        Settings(hover_altitude_mode="ned", hover_agl_m=0.22, scan_agl_m=2.0),
    )
    v = FakeVehicle()
    v.connected = True
    m = Mission(v)
    m.state.detections = [
        Detection(id="w1", class_name="dandelion", north_m=1.0, east_m=2.0, conf=0.9)
    ]
    m.state.confirms = [ConfirmDecision(detection_id="w1", decision="confirm")]
    await m._visit_confirmed()
    assert v.goto_agls == []
    assert any(abs(g[2] - (-0.22)) < 1e-9 for g in v.gotos)


@pytest.mark.asyncio
async def test_offboard_agl_refuses_without_lidar(monkeypatch):
    """Fail closed: no goto_global_agl / pulse when DISTANCE_SENSOR missing."""
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        Settings(hover_altitude_mode="offboard_agl", hover_agl_m=0.22, scan_agl_m=2.0),
    )
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    v._telem.distance_sensor_missing = True
    v._telem.distance_sensor_m = None
    m = Mission(v)
    m.state.detections = [
        Detection(id="w1", class_name="dandelion", north_m=1.0, east_m=2.0, conf=0.9)
    ]
    m.state.confirms = [ConfirmDecision(detection_id="w1", decision="confirm")]
    with pytest.raises(RuntimeError, match="DISTANCE_SENSOR"):
        await m._visit_confirmed()
    assert v.goto_agls == []
    assert v.pulses == 0


@pytest.mark.asyncio
async def test_offboard_agl_refuses_when_distance_none(monkeypatch):
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        Settings(hover_altitude_mode="offboard_agl", hover_agl_m=0.22, scan_agl_m=2.0),
    )
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    v._telem.distance_sensor_missing = False
    v._telem.distance_sensor_m = None
    m = Mission(v)
    m.state.detections = [
        Detection(id="w1", class_name="dandelion", north_m=1.0, east_m=2.0, conf=0.9)
    ]
    m.state.confirms = [ConfirmDecision(detection_id="w1", decision="confirm")]
    with pytest.raises(RuntimeError, match="DISTANCE_SENSOR"):
        await m._visit_confirmed()
    assert v.goto_agls == []
