"""Mission state machine: fence → scan → confirm → visit/pulse → RTL.

Unconfirmed detections are never sprayed. Hover AGL uses DISTANCE_SENSOR or
``missing`` (SIH has none). See ``docs/architecture.md``.
"""

from __future__ import annotations

import asyncio
import logging
import math
from statistics import median

import httpx

from weed_spray.vision.classes import CLASSES
from weed_spray.vision.project import project_nadir

from .config import settings
from .geo import lawnmower_waypoints
from .models import (
    EXPORT_PHASE,
    AppState,
    ArmRequest,
    ConfirmDecision,
    ConfirmEvent,
    ConfirmRequest,
    Detection,
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
        self._yolo_task: asyncio.Task | None = None
        self._yolo_hits: dict[str, list[tuple[float, float]]] = {}
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

    def observe_pixels(self, pixels: list[dict]) -> None:
        """Project scan-time pixel rows into unconfirmed ``y*`` detections.

        Does nothing unless ``WEED_YOLO_GEOREFERENCE`` is on and the phase is
        ``scanning``. Never sets ``confirmed``. Missing or non-live scan-height lidar or
        an unset lens sets ``last_error`` and does not use baro or local z.
        A locked id (confirm or reject already recorded) does not move.
        """
        if not settings.yolo_georeference or self.state.phase != MissionPhase.scanning:
            return
        telem = self.vehicle.telemetry
        if not telem.distance_sensor_stream_alive or telem.distance_scan_m is None:
            self.state.last_error = "YOLO skipped: scan-height lidar missing"
            return
        if settings.cam_hfov_deg is None:
            self.state.last_error = "YOLO skipped: camera HFOV unset"
            return
        if telem.north_m is None or telem.east_m is None or telem.heading_deg is None:
            self.state.last_error = "YOLO skipped: vehicle north/east missing"
            return

        fence = self.state.fence
        fence_tuple = None
        if fence is not None:
            fence_tuple = (fence.north_m, fence.south_m, fence.east_m, fence.west_m)
        locked = {event.detection_id for event in self.state.confirms}
        by_id = {det.id: det for det in self.state.detections}
        placed = False
        for row in pixels:
            if "cx" not in row or row.get("class") not in CLASSES:
                continue
            conf = float(row.get("conf", 0.0))
            width = float(row.get("w", 0.0))
            height = float(row.get("h", 0.0))
            if conf < settings.yolo_conf or min(width, height) * settings.yolo_imgsz < 20:
                continue
            point = project_nadir(
                cx=float(row["cx"]),
                cy=float(row["cy"]),
                frame_w=int(row.get("frame_w") or settings.yolo_imgsz),
                frame_h=int(row.get("frame_h") or settings.yolo_imgsz),
                hfov_deg=settings.cam_hfov_deg,
                height_m=telem.distance_scan_m,
                north_m=telem.north_m,
                east_m=telem.east_m,
                heading_deg=telem.heading_deg,
                fence=fence_tuple,
            )
            if point is None:
                continue
            north, east = point
            match = self._match_yolo(by_id, str(row["class"]), north, east)
            if match is None:
                det_id = self._next_yolo_id(by_id)
                by_id[det_id] = Detection(
                    id=det_id,
                    class_name=str(row["class"]),
                    north_m=north,
                    east_m=east,
                    conf=conf,
                )
                self._yolo_hits[det_id] = [(north, east)]
                placed = True
                continue
            if match in locked:
                continue
            hits = self._yolo_hits.setdefault(match, [])
            hits.append((north, east))
            del hits[:-5]
            det = by_id[match]
            det.north_m = float(median(item[0] for item in hits))
            det.east_m = float(median(item[1] for item in hits))
            det.conf = max(det.conf, conf)
            placed = True
        self.state.detections = list(by_id.values())
        if placed:
            self.state.last_error = None

    def _match_yolo(
        self,
        by_id: dict[str, Detection],
        class_name: str,
        north: float,
        east: float,
    ) -> str | None:
        """Nearest same-class ``y*`` id within ``yolo_assoc_m``, or None."""
        best: str | None = None
        best_d = settings.yolo_assoc_m
        for det in by_id.values():
            if not det.id.startswith("y") or det.class_name != class_name:
                continue
            dist = math.hypot(det.north_m - north, det.east_m - east)
            if dist <= best_d and (best is None or dist < best_d):
                best = det.id
                best_d = dist
        return best

    def _next_yolo_id(self, by_id: dict[str, Detection]) -> str:
        """Next ``y1``, ``y2``, … that does not collide with injector ids."""
        nums = [
            int(det_id[1:]) for det_id in by_id if det_id.startswith("y") and det_id[1:].isdigit()
        ]
        return f"y{max(nums, default=0) + 1}"

    def stamp_yolo_ids(self, pixels: list[dict]) -> list[dict]:
        """Copy pixel rows and attach matched ``y*`` ids for overlay click-to-select.

        Vision never owns mission ids. The dashboard only calls ``onPick`` when
        ``box.id`` is set, so ``/vision/boxes`` joins each live pixel to the
        nearest same-class ``y*`` track using the same nadir projection as
        ``observe_pixels``. Georeference off, or missing live scan lidar /
        lens / pose, leaves rows without ``id`` (checkbox-only selection).
        """
        out: list[dict] = []
        for row in pixels:
            stamped = dict(row)
            track_id = self._yolo_id_for_pixel(row)
            if track_id is not None:
                stamped["id"] = track_id
            out.append(stamped)
        return out

    def _yolo_id_for_pixel(self, row: dict) -> str | None:
        """Project one pixel and return the matched ``y*`` id, or None."""
        if not settings.yolo_georeference:
            return None
        if "cx" not in row or row.get("class") not in CLASSES:
            return None
        telem = self.vehicle.telemetry
        if not telem.distance_sensor_stream_alive or telem.distance_scan_m is None:
            return None
        if settings.cam_hfov_deg is None:
            return None
        if telem.north_m is None or telem.east_m is None or telem.heading_deg is None:
            return None
        conf = float(row.get("conf", 0.0))
        width = float(row.get("w", 0.0))
        height = float(row.get("h", 0.0))
        if conf < settings.yolo_conf or min(width, height) * settings.yolo_imgsz < 20:
            return None
        fence = self.state.fence
        fence_tuple = None
        if fence is not None:
            fence_tuple = (fence.north_m, fence.south_m, fence.east_m, fence.west_m)
        point = project_nadir(
            cx=float(row["cx"]),
            cy=float(row["cy"]),
            frame_w=int(row.get("frame_w") or settings.yolo_imgsz),
            frame_h=int(row.get("frame_h") or settings.yolo_imgsz),
            hfov_deg=settings.cam_hfov_deg,
            height_m=telem.distance_scan_m,
            north_m=telem.north_m,
            east_m=telem.east_m,
            heading_deg=telem.heading_deg,
            fence=fence_tuple,
        )
        if point is None:
            return None
        north, east = point
        by_id = {det.id: det for det in self.state.detections}
        return self._match_yolo(by_id, str(row["class"]), north, east)

    async def _fetch_yolo_pixels(self) -> list[dict]:
        """GET the vision worker's current detections. Raises if it is down."""
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get(f"{settings.vision_url}/detections")
            response.raise_for_status()
        body = response.json()
        rows = body.get("detections", [])
        return rows if isinstance(rows, list) else []

    async def _watch_yolo(self) -> None:
        """Poll pixels while scanning. A dead vision worker does not stop the lawnmower."""
        while self.state.phase == MissionPhase.scanning:
            try:
                pixels = await self._fetch_yolo_pixels()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001  camera blink must not abort scan
                log.warning("vision poll failed: %s", exc)
            else:
                self.observe_pixels(pixels)
            await asyncio.sleep(0.2)

    async def _stop_yolo_watch(self) -> None:
        """Cancel the scan poll if it is still running."""
        task = self._yolo_task
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

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
        self._yolo_task = None
        if settings.yolo_georeference:
            self._yolo_task = asyncio.create_task(self._watch_yolo())
        try:
            await asyncio.sleep(0)
            for north, east in lawnmower_waypoints(self.state.fence, settings.lawnmower_spacing_m):
                if self.state.phase == MissionPhase.killed:
                    return
                await self.vehicle.goto_ned(north, east, down_scan, settle_s=3.0)
            self._set_phase(MissionPhase.awaiting_confirm)
        finally:
            await self._stop_yolo_watch()

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
        """Visit confirmed plants: Offboard XY at scan height, lidar hover, pulse.

        Restarts Offboard hold first (confirm gap drops setpoints; PX4 RTL-climbs).
        ``offboard_agl``: stream_alive, step NED to -1 m then hover, wait lidar
        in band, then ``goto_global_agl``. SIH ``ned``: NED hover only. Hover
        AGL proof is DISTANCE_SENSOR, never local ``z``.
        """
        confirmed_ids = {c.detection_id for c in self.state.confirms if c.decision == "confirm"}
        targets = [d for d in self.state.detections if d.id in confirmed_ids]
        if not targets:
            raise RuntimeError("no confirmed detections")
        down_scan = -settings.scan_agl_m
        down_hover = -(settings.hover_agl_m + settings.lidar_mount_down_m)
        # Confirm gap sends no Offboard setpoints; PX4 times out and RTL-climbs (~30 m).
        first = targets[0]
        await self.vehicle.start_offboard_hold(first.north_m, first.east_m, down_scan)
        for det in targets:
            if self.state.phase == MissionPhase.killed:
                return
            self._set_phase(MissionPhase.visiting)
            await self.vehicle.goto_ned(det.north_m, det.east_m, down_scan, settle_s=4.0)
            det.visited = True
            self._set_phase(MissionPhase.hovering)
            if settings.hover_altitude_mode == "offboard_agl":
                if not settings.lidar_expected:
                    raise RuntimeError(
                        "offboard_agl refused: WEED_LIDAR_EXPECTED must be set "
                        "(SIH has no belly lidar; Gazebo sets it explicitly)"
                    )
                telem = self.vehicle.telemetry
                if telem.lat is None or telem.lon is None:
                    raise RuntimeError("offboard_agl hover needs lat/lon telemetry")
                # XY at scan height. NED descend to gear+2 in; lidar (not z) is the
                # in-band proof. Then AGL setpoint to hold. TERRAIN_ALT alone does
                # not descend on this gz airframe (issue #19 UAT).
                if not telem.distance_sensor_stream_alive:
                    raise RuntimeError(
                        "offboard_agl refused: DISTANCE_SENSOR stream not alive "
                        "(need a scan-height sample with relative_alt before hover)"
                    )
                # Step down so Gazebo does not slam through the hover band.
                await self.vehicle.goto_ned(det.north_m, det.east_m, -1.0, settle_s=4.0)
                await self.vehicle.goto_ned(det.north_m, det.east_m, down_hover, settle_s=8.0)
                try:
                    await self.vehicle.wait_lidar_hover_band(
                        settings.hover_min_m,
                        settings.hover_max_m,
                        timeout_s=45.0,
                        north=det.north_m,
                        east=det.east_m,
                        down=down_hover,
                    )
                except TimeoutError as exc:
                    raise RuntimeError(f"offboard_agl refused: {exc}") from exc
                await self.vehicle.goto_global_agl(
                    telem.lat, telem.lon, settings.hover_agl_m, settle_s=2.0
                )
                telem = self.vehicle.telemetry
                if telem.distance_sensor_missing or telem.distance_sensor_m is None:
                    raise RuntimeError("offboard_agl refused: no trusted hover AGL after AGL hold")
                if not (settings.hover_min_m <= telem.distance_sensor_m <= settings.hover_max_m):
                    raise RuntimeError(
                        f"offboard_agl refused: hover AGL out of band ({telem.distance_sensor_m} m)"
                    )
            else:
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
