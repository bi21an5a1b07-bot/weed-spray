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


def test_sih_mirror_does_not_count_as_stream_alive():
    assert is_relative_alt_mirror(2.0, 2.0) is True
    assert is_relative_alt_mirror(11.97, 12.0) is True
    telem = Telemetry()
    apply_distance_sample(telem, 2.0, relative_alt_m=2.0)
    assert telem.distance_sensor_stream_alive is False
    assert telem.distance_sensor_missing is True


def test_sih_hover_mirror_does_not_count_as_stream_alive():
    """Hover-height SIH mirror (~0.22) must not open TERRAIN_ALT."""
    telem = Telemetry()
    apply_distance_sample(telem, 0.22, relative_alt_m=0.22)
    assert telem.distance_sensor_stream_alive is False
    # short-range trust bar still keeps the reading for sampling / ned path
    assert telem.distance_sensor_m == 0.22
    assert telem.distance_sensor_missing is False


def test_non_mirror_scan_height_marks_stream_alive():
    telem = Telemetry()
    apply_distance_sample(telem, 2.0, relative_alt_m=2.8)
    assert telem.distance_sensor_stream_alive is True
    assert telem.distance_sensor_m is None  # still outside short-range trust


def test_absurd_high_non_mirror_does_not_mark_stream_alive():
    """SIH high-while-low junk must not open TERRAIN_ALT."""
    telem = Telemetry()
    apply_distance_sample(telem, 12.0, relative_alt_m=0.22)
    assert telem.distance_sensor_stream_alive is False


@pytest.mark.asyncio
async def test_goto_global_agl_records_lat_lon_agl():
    v = FakeVehicle()
    await v.goto_global_agl(40.1, -105.2, 0.22, settle_s=0.0)
    assert v.goto_agls == [(40.1, -105.2, 0.22)]


@pytest.mark.asyncio
async def test_visit_offboard_agl_ned_approach_then_agl_hold(monkeypatch):
    """NED to hover first; AGL hold only after in-band trusted lidar."""
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
    # prior non-mirror sample (e.g. scan height with baro offset)
    v._telem.distance_sensor_stream_alive = True
    v.agl_after_descend_m = 0.22
    m = _mission(v)
    await m._visit_confirmed()
    assert v.goto_agls[-1] == (40.01, -105.01, 0.22)
    # NED hover approach happened before AGL
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
async def test_offboard_agl_refuses_agl_when_sih_mirror_only(monkeypatch):
    """SIH mirrors: NED approach ok, but no trusted band → no goto_global_agl / pulse."""
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        Settings(hover_altitude_mode="offboard_agl", hover_agl_m=0.22, scan_agl_m=2.0),
    )
    v = FakeVehicle()
    v.connected = True
    v._telem.lat = 40.01
    v._telem.lon = -105.01
    v.agl_after_descend_m = None  # still missing after NED hover
    m = _mission(v)
    with pytest.raises(RuntimeError, match="trusted hover AGL"):
        await m._visit_confirmed()
    assert v.goto_agls == []
    assert v.pulses == 0


@pytest.mark.asyncio
async def test_offboard_agl_refuses_pulse_when_out_of_band(monkeypatch):
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
    v.agl_after_descend_m = 0.50
    m = _mission(v)
    with pytest.raises(RuntimeError, match="band"):
        await m._visit_confirmed()
    assert v.goto_agls == []
    assert v.pulses == 0


@pytest.mark.asyncio
async def test_offboard_agl_refuses_when_only_hover_sih_mirror(monkeypatch):
    """In-band SIH hover mirror without prior non-mirror stream → no AGL / pulse."""
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
    v._telem.relative_alt_m = 0.22
    v._telem.distance_sensor_stream_alive = False
    v.agl_after_descend_m = 0.22  # looks in-band but stream never non-mirror
    m = _mission(v)
    with pytest.raises(RuntimeError, match="stream"):
        await m._visit_confirmed()
    assert v.goto_agls == []
    assert v.pulses == 0


def test_none_relative_alt_does_not_unlock_stream_alive():
    telem = Telemetry()
    apply_distance_sample(telem, 2.0, relative_alt_m=None)
    assert telem.distance_sensor_stream_alive is False


def test_lagging_relative_alt_does_not_unlock_stream_alive():
    """ds=2 while rel still at hover (~0.22) must not sticky-unlock."""
    telem = Telemetry()
    apply_distance_sample(telem, 2.0, relative_alt_m=0.22)
    assert telem.distance_sensor_stream_alive is False


def test_mirror_clears_sticky_stream_alive():
    telem = Telemetry()
    apply_distance_sample(telem, 2.0, relative_alt_m=2.8)  # non-mirror scan
    assert telem.distance_sensor_stream_alive is True
    apply_distance_sample(telem, 0.22, relative_alt_m=0.22)  # hover mirror
    assert telem.distance_sensor_stream_alive is False


@pytest.mark.asyncio
async def test_offboard_agl_latches_stream_before_hover_mirrors(monkeypatch):
    """Latch scan-height stream_ok before NED hover clears telem.stream_alive."""
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
    v.agl_after_descend_m = 0.22

    async def descend_and_clear(north, east, down, settle_s=0.0):
        v.gotos.append((north, east, down))
        if abs(down) <= 1.0:
            v._apply_descend_reading()
            # SIH/flat hover mirror would clear sticky telem flag
            v._telem.distance_sensor_stream_alive = False

    v.goto_ned = descend_and_clear  # type: ignore[method-assign]
    m = _mission(v)
    await m._visit_confirmed()
    assert v.goto_agls[-1] == (40.01, -105.01, 0.22)
    assert v.pulses == 1
