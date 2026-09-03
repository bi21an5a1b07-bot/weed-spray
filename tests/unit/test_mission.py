"""Mission FSM: inject/confirm, unconfirmed never sprayed, RC vs dashboard, failsafes."""

import asyncio

import pytest

from tests.fakes import FakeVehicle
from weed_spray.backend.mission import Mission
from weed_spray.backend.models import (
    ArmRequest,
    ConfirmRequest,
    Detection,
    FenceBox,
    InjectRequest,
    MissionPhase,
)


def _mission() -> tuple[Mission, FakeVehicle]:
    """Fresh Mission + FakeVehicle pair (not connected until a test calls connect)."""
    vehicle = FakeVehicle()
    return Mission(vehicle), vehicle


def _dandelion(det_id: str = "w1") -> Detection:
    """One dandelion at the harness fixture NED (6 m north, 4 m east)."""
    return Detection(id=det_id, class_name="dandelion", north_m=6.0, east_m=4.0)


@pytest.mark.asyncio
async def test_inject_rejects_unknown_class():
    mission, _ = _mission()
    with pytest.raises(ValueError, match="unknown class"):
        mission.inject(
            InjectRequest(
                detections=[Detection(id="x", class_name="crabgrass", north_m=0, east_m=0)]
            )
        )


@pytest.mark.asyncio
async def test_confirm_unknown_id():
    mission, _ = _mission()
    mission.inject(InjectRequest(detections=[_dandelion()]))
    with pytest.raises(ValueError, match="unknown ids"):
        mission.confirm(ConfirmRequest(ids=["nope"]))


@pytest.mark.asyncio
async def test_confirm_subset_does_not_mark_others():
    mission, _ = _mission()
    mission.inject(
        InjectRequest(
            detections=[
                _dandelion("w1"),
                Detection(id="w2", class_name="clover", north_m=1, east_m=1),
            ]
        )
    )
    mission.confirm(ConfirmRequest(ids=["w1"]))
    by_id = {d.id: d for d in mission.state.detections}
    assert by_id["w1"].confirmed is True
    assert by_id["w2"].confirmed is False
    assert [c.detection_id for c in mission.state.confirms] == ["w1"]


@pytest.mark.asyncio
async def test_reject_clears_confirm():
    mission, _ = _mission()
    mission.inject(InjectRequest(detections=[_dandelion()]))
    mission.confirm(ConfirmRequest(ids=["w1"]))
    mission.confirm(ConfirmRequest(decisions=[{"detection_id": "w1", "decision": "reject"}]))
    assert mission.state.detections[0].confirmed is False
    assert mission.state.confirms[-1].decision == "reject"


@pytest.mark.asyncio
async def test_scan_requires_fence_and_connection():
    mission, _vehicle = _mission()
    await mission.start_scan(ArmRequest(source="dashboard"))
    await asyncio.wait_for(mission._run_task, timeout=2)
    assert mission.state.phase == MissionPhase.error
    assert "geofence" in (mission.state.last_error or "")

    mission2, vehicle2 = _mission()
    vehicle2.connected = False
    mission2.state.fence = FenceBox()
    # connected flag on vehicle is still False
    await mission2.start_scan()
    await asyncio.wait_for(mission2._run_task, timeout=2)
    assert mission2.state.phase == MissionPhase.error


@pytest.mark.asyncio
async def test_dashboard_scan_then_visit_confirmed_only():
    mission, vehicle = _mission()
    await mission.connect()
    await mission.set_fence(FenceBox())
    mission.inject(
        InjectRequest(
            detections=[
                _dandelion("w1"),
                Detection(id="w2", class_name="clover", north_m=8, east_m=-3),
            ]
        )
    )
    await mission.start_scan(ArmRequest(source="dashboard"))
    await asyncio.wait_for(mission._run_task, timeout=2)
    assert mission.state.phase == MissionPhase.awaiting_confirm
    assert vehicle.armed_takeoff == 1
    assert vehicle.waited_in_air == 0

    mission.confirm(ConfirmRequest(ids=["w1"]))
    await mission.visit_now()
    await asyncio.wait_for(mission._run_task, timeout=2)
    by_id = {d.id: d for d in mission.state.detections}
    assert by_id["w1"].visited and by_id["w1"].sprayed
    assert not by_id["w2"].visited and not by_id["w2"].sprayed
    assert vehicle.pulses == 1
    assert len(mission.state.pump_pulses) == 1
    assert mission.state.pump_pulses[0].duration_s == 0.75
    assert mission.state.hover_agl_m[0].missing is True
    assert mission.state.phase == MissionPhase.rtl
    assert any(e.type == "rtl" for e in mission.state.pump_off_events)


@pytest.mark.asyncio
async def test_rc_first_waits_in_air():
    mission, vehicle = _mission()
    await mission.connect()
    await mission.set_fence(FenceBox())
    await mission.start_scan(ArmRequest(source="rc"))
    await asyncio.wait_for(mission._run_task, timeout=2)
    assert vehicle.waited_in_air == 1
    assert vehicle.armed_takeoff == 0


@pytest.mark.asyncio
async def test_connect_clears_stale_last_error():
    mission, _ = _mission()
    mission.state.last_error = "Offboard plugin has not been initialized!"
    await mission.connect()
    assert mission.state.last_error is None
    assert mission.state.phase == MissionPhase.connected


@pytest.mark.asyncio
async def test_visit_rejects_when_disconnected():
    mission, vehicle = _mission()
    vehicle.connected = False
    with pytest.raises(RuntimeError, match="not connected"):
        await mission.visit_now()


@pytest.mark.asyncio
async def test_visit_without_confirm_fails():
    mission, _ = _mission()
    await mission.connect()
    await mission.set_fence(FenceBox())
    mission.inject(InjectRequest(detections=[_dandelion()]))
    await mission.visit_now()
    await asyncio.wait_for(mission._run_task, timeout=2)
    assert mission.state.phase == MissionPhase.error
    assert "no confirmed" in (mission.state.last_error or "")


@pytest.mark.asyncio
async def test_kill_and_people_hold_command_pump_off():
    mission, vehicle = _mission()
    await mission.connect()
    await mission.kill()
    assert vehicle.kills == 1
    assert mission.state.phase == MissionPhase.killed
    assert mission.state.pump_off_events[-1].type == "kill"

    mission2, vehicle2 = _mission()
    await mission2.connect()
    await mission2.hold_for_people()
    assert any(e.type == "people" for e in mission2.state.pump_off_events)
    assert vehicle2.pump_value == 0.0


@pytest.mark.asyncio
async def test_failsafe_ignored_when_idle():
    mission, _vehicle = _mission()
    await mission._on_failsafe("rc_loss")
    assert mission.state.pump_off_events == []

    mission.state.phase = MissionPhase.scanning
    await mission._on_failsafe("rc_loss")
    assert mission.state.pump_off_events[-1].type == "rc_loss"


@pytest.mark.asyncio
async def test_run_log_schema():
    mission, _ = _mission()
    await mission.connect()
    await mission.set_fence(FenceBox(north_m=10, south_m=0, east_m=10, west_m=0))
    log = mission.run_log()
    assert log["kind"] == "sitl"
    assert log["geofence"] == {"n": 10, "e": 10, "s": 0, "w": 0}
    assert "14540" in log["compose"]
    assert log["arm_source"] == "missing"
    for key in (
        "detections",
        "confirms",
        "hover_agl_m",
        "pump_pulses",
        "pump_off_events",
        "phase",
    ):
        assert key in log


@pytest.mark.asyncio
async def test_scan_while_running_raises():
    mission, vehicle = _mission()
    await mission.connect()
    await mission.set_fence(FenceBox())
    gate = asyncio.Event()

    async def blocked_goto(*_a, **_k):
        await gate.wait()

    vehicle.goto_ned = blocked_goto  # type: ignore[method-assign]
    await mission.start_scan()
    await asyncio.sleep(0)
    with pytest.raises(RuntimeError, match="already running"):
        await mission.start_scan()
    with pytest.raises(RuntimeError, match="scan still running"):
        await mission.visit_now()
    gate.set()
    await asyncio.wait_for(mission._run_task, timeout=2)
