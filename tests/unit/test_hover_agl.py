"""Offboard AGL hover seam (issue #19) — FakeVehicle only; no live PX4."""

import pytest

from tests.fakes import FakeVehicle
from weed_spray.backend.config import Settings
from weed_spray.backend.mission import Mission
from weed_spray.backend.models import ConfirmDecision, Detection, Telemetry
from weed_spray.backend.vehicle import apply_distance_sample, is_relative_alt_mirror


def _mission(v: FakeVehicle) -> Mission:
    m = Mission(v)
    m.state.detections = [
        Detection(id="w1", class_name="dandelion", north_m=1.0, east_m=2.0, conf=0.9)
    ]
    m.state.confirms = [ConfirmDecision(detection_id="w1", decision="confirm")]
    return m


def _agl_settings(**kwargs) -> Settings:
    base = dict(
        hover_altitude_mode="offboard_agl",
        lidar_expected=True,
        hover_agl_m=0.22,
        hover_min_m=0.15,
        hover_max_m=0.30,
        scan_agl_m=2.0,
    )
    base.update(kwargs)
    return Settings(**base)


def test_sih_mirror_helper_still_detects_scan_lock():
    assert is_relative_alt_mirror(2.0, 2.0) is True
    assert is_relative_alt_mirror(11.97, 12.0) is True


def test_flat_gazebo_scan_height_unlocks_stream_alive():
    """ds≈relative_alt at scan height must unlock (real belly lidar on flat ground)."""
    telem = Telemetry()
    apply_distance_sample(telem, 2.05, relative_alt_m=1.98)
    assert telem.distance_sensor_stream_alive is True
    assert telem.distance_sensor_m is None  # outside short-range trust


def test_none_relative_alt_does_not_unlock_stream_alive():
    telem = Telemetry()
    apply_distance_sample(telem, 2.0, relative_alt_m=None)
    assert telem.distance_sensor_stream_alive is False


def test_lagging_relative_alt_does_not_unlock_stream_alive():
    telem = Telemetry()
    apply_distance_sample(telem, 2.0, relative_alt_m=0.22)
    assert telem.distance_sensor_stream_alive is False


@pytest.mark.asyncio
async def test_goto_global_agl_records_lat_lon_agl():
    v = FakeVehicle()
    await v.goto_global_agl(40.1, -105.2, 0.22, settle_s=0.0)
    assert v.goto_agls == [(40.1, -105.2, 0.22)]


@pytest.mark.asyncio
async def test_visit_offboard_agl_happy_path_via_apply_sample(monkeypatch):
    """Drive stream_alive through apply_distance_sample (flat ds≈rel), not hand-set."""
    monkeypatch.setattr("weed_spray.backend.mission.settings", _agl_settings())
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    apply_distance_sample(v._telem, 2.05, relative_alt_m=1.98)
    assert v._telem.distance_sensor_stream_alive is True
    v.agl_after_descend_m = 0.22
    m = _mission(v)
    await m._visit_confirmed()
    assert v.goto_agls[-1] == (40.01, -105.01, 0.22)
    assert any(abs(g[2] - (-0.22)) < 1e-9 for g in v.gotos)
    assert v.pulses == 1


@pytest.mark.asyncio
async def test_visit_default_ned_does_not_call_agl(monkeypatch):
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        Settings(hover_altitude_mode="ned", hover_agl_m=0.22, scan_agl_m=2.0),
    )
    v = FakeVehicle()
    v.connected = True
    m = _mission(v)
    await m._visit_confirmed()
    assert v.goto_agls == []
    assert any(abs(g[2] - (-0.22)) < 1e-9 for g in v.gotos)


@pytest.mark.asyncio
async def test_offboard_agl_refuses_without_lidar_expected(monkeypatch):
    """SIH default: offboard_agl without WEED_LIDAR_EXPECTED → no TERRAIN_ALT."""
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        _agl_settings(lidar_expected=False),
    )
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    apply_distance_sample(v._telem, 2.05, relative_alt_m=1.98)
    v.agl_after_descend_m = 0.22
    m = _mission(v)
    with pytest.raises(RuntimeError, match="LIDAR_EXPECTED"):
        await m._visit_confirmed()
    assert v.goto_agls == []
    assert v.pulses == 0


@pytest.mark.asyncio
async def test_offboard_agl_refuses_when_stream_dead(monkeypatch):
    monkeypatch.setattr("weed_spray.backend.mission.settings", _agl_settings())
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    v._telem.distance_sensor_stream_alive = False
    v.agl_after_descend_m = 0.22
    m = _mission(v)
    with pytest.raises(RuntimeError, match="stream"):
        await m._visit_confirmed()
    assert v.goto_agls == []
    assert v.pulses == 0


@pytest.mark.asyncio
async def test_offboard_agl_refuses_when_missing_after_descend(monkeypatch):
    monkeypatch.setattr("weed_spray.backend.mission.settings", _agl_settings())
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    apply_distance_sample(v._telem, 2.05, relative_alt_m=1.98)
    v.agl_after_descend_m = None
    m = _mission(v)
    with pytest.raises(RuntimeError, match="trusted hover AGL"):
        await m._visit_confirmed()
    assert v.goto_agls == []
    assert v.pulses == 0


@pytest.mark.asyncio
async def test_offboard_agl_refuses_pulse_when_out_of_band(monkeypatch):
    monkeypatch.setattr("weed_spray.backend.mission.settings", _agl_settings())
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    apply_distance_sample(v._telem, 2.05, relative_alt_m=1.98)
    v.agl_after_descend_m = 0.50
    m = _mission(v)
    with pytest.raises(RuntimeError, match="band"):
        await m._visit_confirmed()
    assert v.goto_agls == []
    assert v.pulses == 0
