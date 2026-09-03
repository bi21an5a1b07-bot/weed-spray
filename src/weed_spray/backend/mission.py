"""Mission state machine: fence → scan → confirm → visit/pulse → RTL.

Unconfirmed detections are never sprayed. Hover AGL uses DISTANCE_SENSOR or
``missing`` (SIH has none). See ``docs/architecture.md``.
"""

from __future__ import annotations

import asyncio
import logging

from weed_spray.vision.classes import CLASSES

from .config import settings
from .geo import lawnmower_waypoints
from .models import (
    EXPORT_PHASE,
    AppState,
    ArmRequest,
    ConfirmDecision,
    ConfirmEvent,
    ConfirmRequest,
    FenceBox,
    HoverSample,
    InjectRequest,
    MissionPhase,
    PhaseEvent,
    PumpPulse,
    utc_now,
)
from .vehicle import Vehicle

log = logging.getLogger("weed_spray.mission")


class Mission:
    """Owns ``AppState`` and sequences Vehicle calls for one flight."""

    def __init__(self, vehicle: Vehicle) -> None:
        """Bind a Vehicle (or FakeVehicle) and register the failsafe callback."""
        self.vehicle = vehicle
        self.state = AppState(
            rtsp_url=settings.rtsp_url,
            webrtc_url=settings.webrtc_url,
            mavsdk_address=settings.mavsdk_address,
        )
        self._run_task: asyncio.Task | None = None
        self.vehicle.on_failsafe = self._on_failsafe

    def snapshot(self) -> AppState:
        """Deep copy of mission state plus live telemetry."""
        snap = self.state.model_copy(deep=True)
        snap.telemetry = self.vehicle.telemetry
        return snap

    def _set_phase(self, phase: MissionPhase) -> None:
        """Set internal phase and append an exported sitl_template phase row if mapped."""
        self.state.phase = phase
        exported = EXPORT_PHASE.get(phase)
        if exported:
            self.state.phase_log.append(PhaseEvent(name=exported))

    async def _on_failsafe(self, kind: str) -> None:
        """Pump off unless already idle/killed. ``kind`` becomes PumpOffEvent.type."""
        if self.state.phase in {MissionPhase.killed, MissionPhase.idle}:
            return
        event = await self.vehicle.pump_off(kind)
        self.state.pump_off_events.append(event)
        log.warning("failsafe %s pump off", kind)

    async def connect(self) -> None:
        """Connect MAVSDK and stamp ``t_start``. Clears a stale ``last_error``."""
        self._set_phase(MissionPhase.connecting)
        self.state.t_start = utc_now()
        await self.vehicle.connect()
        self.state.last_error = None
        self._set_phase(MissionPhase.connected)

    async def set_fence(self, box: FenceBox) -> None:
        """Upload the typed yard rectangle to PX4 and store it on state."""
        await self.vehicle.upload_fence(box)
        self.state.fence = box
        self._set_phase(MissionPhase.fence_set)

    def inject(self, req: InjectRequest) -> None:
        """Merge detections by id. Rejects classes outside the frozen map."""
        existing = {d.id: d for d in self.state.detections}
        for det in req.detections:
            if det.class_name not in CLASSES:
                raise ValueError(f"unknown class {det.class_name}")
            if not det.t:
                det.t = utc_now()
            existing[det.id] = det
        self.state.detections = list(existing.values())

    def confirm(self, req: ConfirmRequest) -> None:
        """Record confirm/reject events. ``ids`` are confirms. Does not pulse the pump."""
        decisions = list(req.decisions)
        for det_id in req.ids:
            decisions.append(ConfirmDecision(detection_id=det_id, decision="confirm"))
        known = {d.id for d in self.state.detections}
        unknown = {d.detection_id for d in decisions} - known
        if unknown:
            raise ValueError(f"unknown ids {sorted(unknown)}")
        by_id = {d.id: d for d in self.state.detections}
        for item in decisions:
            ev = ConfirmEvent(detection_id=item.detection_id, decision=item.decision)
            self.state.confirms.append(ev)
            if item.decision == "confirm":
                by_id[item.detection_id].confirmed = True
            else:
                by_id[item.detection_id].confirmed = False
        self._set_phase(MissionPhase.awaiting_confirm)

    async def kill(self) -> None:
        """Operator kill: pump off, cancel scan/visit task."""
        event = await self.vehicle.kill()
        self.state.pump_off_events.append(event)
        self._set_phase(MissionPhase.killed)
        if self._run_task and not self._run_task.done():
            self._run_task.cancel()

    async def hold_for_people(self) -> None:
        """People/pets abort: pump off and PX4 Hold."""
        event = await self.vehicle.pump_off("people")
        self.state.pump_off_events.append(event)
        try:
            await self.vehicle.drone.action.hold()
        except Exception as exc:  # noqa: BLE001
            log.warning("hold: %s", exc)
        self._set_phase(MissionPhase.killed)

    async def rtl(self) -> None:
        """Pump off then return-to-launch."""
        event = await self.vehicle.pump_off("rtl")
        self.state.pump_off_events.append(event)
        await self.vehicle.rtl()
        self._set_phase(MissionPhase.rtl)

    async def start_scan(self, arm: ArmRequest | None = None) -> None:
        """Start background lawnmower at scan AGL. Raises if a task is already running."""
        if self._run_task and not self._run_task.done():
            raise RuntimeError("mission already running")
        if arm:
            self.state.arm_source = arm.source
        elif not self.state.arm_source:
            self.state.arm_source = "dashboard"
        self._run_task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        """Wrap ``_run_inner`` so errors pump-off and set phase ``error``."""
        try:
            await self._run_inner()
        except asyncio.CancelledError:
            log.info("mission cancelled")
            raise
        except Exception as exc:
            log.exception("mission failed")
            self.state.last_error = str(exc)
            self._set_phase(MissionPhase.error)
            try:
                event = await self.vehicle.pump_off("mission_error")
                self.state.pump_off_events.append(event)
            except Exception as pump_exc:  # noqa: BLE001  already in error
                log.warning("pump off after mission error failed: %s", pump_exc)

    async def _run_inner(self) -> None:
        """Takeoff (RC- or dashboard-first), Offboard, lawnmower, then await confirm."""
        if self.state.fence is None:
            raise RuntimeError("set a geofence first")
        if not self.vehicle.connected:
            raise RuntimeError("not connected")

        self._set_phase(MissionPhase.taking_off)
        if self.state.arm_source == "rc":
            await self.vehicle.wait_in_air()
        else:
            await self.vehicle.arm_and_takeoff(settings.scan_agl_m)
        down_scan = -settings.scan_agl_m
        await self.vehicle.start_offboard_hold(0.0, 0.0, down_scan)

        self._set_phase(MissionPhase.scanning)
        for north, east in lawnmower_waypoints(self.state.fence, settings.lawnmower_spacing_m):
            if self.state.phase == MissionPhase.killed:
                return
            await self.vehicle.goto_ned(north, east, down_scan, settle_s=3.0)

        self._set_phase(MissionPhase.awaiting_confirm)

    async def visit_now(self) -> None:
        """After confirm: visit confirmed ids only. Errors if scan still running."""
        if self._run_task and not self._run_task.done():
            raise RuntimeError("scan still running")
        if not self.vehicle.connected:
            raise RuntimeError("not connected")
        self._run_task = asyncio.create_task(self._visit_then_rtl())

    async def _visit_then_rtl(self) -> None:
        """Visit loop then RTL; pump-off on exception."""
        try:
            await self._visit_confirmed()
            await self.rtl()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            self.state.last_error = str(exc)
            self._set_phase(MissionPhase.error)
            event = await self.vehicle.pump_off("mission_error")
            self.state.pump_off_events.append(event)

    async def _visit_confirmed(self) -> None:
        """XY at 2 m, descend, sample AGL, pulse 0.75 s, climb, next confirmed id."""
        confirmed_ids = {c.detection_id for c in self.state.confirms if c.decision == "confirm"}
        targets = [d for d in self.state.detections if d.id in confirmed_ids]
        if not targets:
            raise RuntimeError("no confirmed detections")
        down_scan = -settings.scan_agl_m
        down_hover = -settings.hover_agl_m
        for det in targets:
            if self.state.phase == MissionPhase.killed:
                return
            self._set_phase(MissionPhase.visiting)
            await self.vehicle.goto_ned(det.north_m, det.east_m, down_scan, settle_s=4.0)
            det.visited = True
            self._set_phase(MissionPhase.hovering)
            await self.vehicle.goto_ned(det.north_m, det.east_m, down_hover, settle_s=3.0)
            telem = self.vehicle.telemetry
            if telem.distance_sensor_missing or telem.distance_sensor_m is None:
                self.state.hover_agl_m.append(
                    HoverSample(detection_id=det.id, agl_m=None, missing=True)
                )
            else:
                self.state.hover_agl_m.append(
                    HoverSample(detection_id=det.id, agl_m=telem.distance_sensor_m, missing=False)
                )
            self._set_phase(MissionPhase.spraying)
            await self.vehicle.pulse_pump(settings.pump_pulse_s)
            self.state.pump_pulses.append(
                PumpPulse(duration_s=settings.pump_pulse_s, detection_id=det.id)
            )
            det.sprayed = True
            await self.vehicle.goto_ned(det.north_m, det.east_m, down_scan, settle_s=2.0)

    def run_log(self) -> dict:
        """Build the JSON object specified by ``bot_files/sitl_template.md``."""
        snap = self.snapshot()
        geofence = None
        if snap.fence:
            geofence = {
                "n": snap.fence.north_m,
                "e": snap.fence.east_m,
                "s": snap.fence.south_m,
                "w": snap.fence.west_m,
            }
        detections = [
            {
                "id": d.id,
                "t": d.t,
                "class": d.class_name,
                "conf": d.conf,
                "x_m": d.north_m,
                "y_m": d.east_m,
            }
            for d in snap.detections
        ]
        hover = []
        for h in snap.hover_agl_m:
            if h.missing:
                hover.append({"t": h.t, "agl_m": "missing", "detection_id": h.detection_id})
            else:
                hover.append({"t": h.t, "agl_m": h.agl_m, "detection_id": h.detection_id})
        return {
            "kind": snap.kind,
            "t_start": snap.t_start,
            "t_end": utc_now(),
            "git": "weed-spray",
            "px4_version": "px4io/px4-sitl sihsim_quadx",
            "arm_source": snap.arm_source or "missing",
            "compose": "px4io/px4-sitl sihsim_quadx + RTSP 8554/cam + backend 8000 + dashboard 8080 + injector 8090 + UDP 14540",
            "geofence": geofence,
            "phase": [p.model_dump() for p in snap.phase_log],
            "detections": detections,
            "confirms": [c.model_dump() for c in snap.confirms],
            "hover_agl_m": hover,
            "pump_pulses": [p.model_dump() for p in snap.pump_pulses],
            "pump_off_events": [e.model_dump() for e in snap.pump_off_events],
        }
