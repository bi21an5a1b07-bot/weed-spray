"""Offboard AGL hover seam (issue #19) — FakeVehicle only; no live PX4."""

import pytest

from tests.fakes import FakeVehicle
from weed_spray.backend.config import Settings
from weed_spray.backend.mission import Mission
from weed_spray.backend.models import ConfirmDecision, Detection


def _mission(v: FakeVehicle) -> Mission:
    m = Mission(v)
    m.state.detections = [
        Detection(id="w1", class_name="dandelion", north_m=1.0, east_m=2.0, conf=0.9)
    ]
    m.state.confirms = [ConfirmDecision(detection_id="w1", decision="confirm")]
    return m


@pytest.mark.asyncio
async def test_goto_global_agl_records_lat_lon_agl():
    v = FakeVehicle()
    await v.goto_global_agl(40.1, -105.2, 0.22, settle_s=0.0)
    assert v.goto_agls == [(40.1, -105.2, 0.22)]


@pytest.mark.asyncio
async def test_visit_uses_offboard_agl_when_stream_alive(monkeypatch):
    """Stream alive at scan height; in-band only after FakeVehicle descend."""
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        Settings(
            hover_altitude_mode="offboard_agl",
            hover_agl_m=0.22,
            hover_min_m=0.15,
            hover_max_m=0.30,
            scan_agl_m=2.0,
        ),
    )
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    # scan height: stream alive, short-range trust missing (like ~2 m lidar)
    v._telem.distance_sensor_stream_alive = True
    v._telem.distance_sensor_missing = True
    v._telem.distance_sensor_m = None
    m = _mission(v)
    await m._visit_confirmed()
    assert v.goto_agls[-1] == (40.01, -105.01, 0.22)
    assert m.state.hover_agl_m[0].missing is False
    assert m.state.hover_agl_m[0].agl_m == pytest.approx(0.22)
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
async def test_offboard_agl_refuses_when_stream_dead(monkeypatch):
    """Pre-goto: no stream → no goto_global_agl / pulse (SIH)."""
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        Settings(hover_altitude_mode="offboard_agl", hover_agl_m=0.22, scan_agl_m=2.0),
    )
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    v._telem.distance_sensor_stream_alive = False
    v._telem.distance_sensor_missing = True
    v._telem.distance_sensor_m = None
    m = _mission(v)
    with pytest.raises(RuntimeError, match="stream"):
        await m._visit_confirmed()
    assert v.goto_agls == []
    assert v.pulses == 0


@pytest.mark.asyncio
async def test_offboard_agl_refuses_pulse_when_out_of_band_after_descend(monkeypatch):
    """After AGL goto, out-of-band trusted reading → no pulse."""
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        Settings(
            hover_altitude_mode="offboard_agl",
            hover_agl_m=0.22,
            hover_min_m=0.15,
            hover_max_m=0.30,
            scan_agl_m=2.0,
        ),
    )
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    v._telem.distance_sensor_stream_alive = True
    v._telem.distance_sensor_missing = True
    v._telem.distance_sensor_m = None
    v.agl_after_descend_m = 0.50  # out of band
    m = _mission(v)
    with pytest.raises(RuntimeError, match="band"):
        await m._visit_confirmed()
    assert v.goto_agls
    assert v.pulses == 0
