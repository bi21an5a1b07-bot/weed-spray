"""MAVSDK wrapper. PX4 listens for offboard APIs on UDP 14540 (we bind)."""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import Awaitable, Callable

from mavsdk import System
from mavsdk.action import ActionError
from mavsdk.geofence import FenceType, GeofenceData, Point, Polygon
from mavsdk.offboard import OffboardError, PositionNedYaw
from mavsdk.telemetry import FlightMode

from .config import settings
from .geo import fence_corners_latlon
from .models import FenceBox, PumpOffEvent, Telemetry

FailsafeHandler = Callable[[str], Awaitable[None]]

log = logging.getLogger("weed_spray.vehicle")


def distance_reading_m(current: object) -> float | None:
    """SIH has no lidar. NaN / non-positive / missing → None (log as missing)."""
    if current is None:
        return None
    try:
        value = float(current)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or value <= 0:
        return None
    return value


class Vehicle:
    """MAVSDK client for one PX4 vehicle.

    Listens on UDP 14540 (PX4 sends offboard traffic there). Does not write
    ``COM_RCL_EXCEPT`` bit 2 or disable ``NAV_RCL_ACT`` (bot_files/px4_offboard.md).
    """

    def __init__(self) -> None:
        """Create a MAVSDK System. Call ``connect`` before any flight command."""
        self.drone = System()
        self.connected = False
        self.home_lat: float | None = None
        self.home_lon: float | None = None
        self.pump_value = 0.0
        self._telem = Telemetry()
        self._tasks: list[asyncio.Task] = []
        self.on_failsafe: FailsafeHandler | None = None
        self._saw_offboard = False
        self._rc_seen = False

    @property
    def telemetry(self) -> Telemetry:
        """Copy of last telemetry plus ``connected`` and ``pump_value``."""
        t = self._telem.model_copy()
        t.connected = self.connected
        t.pump_value = self.pump_value
        return t

    async def connect(self, address: str = settings.mavsdk_address) -> None:
        """Wait for a MAVSDK heartbeat, home position, then start trackers."""
        log.info("MAVSDK connecting %s", address)
        await self.drone.connect(system_address=address)
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                self.connected = True
                break
        await self._wait_global_position()
        # bot_files/px4_offboard.md: do not invent COM_* / NAV_RCL_ACT / COM_RCL_EXCEPT.
        self._tasks = [
            asyncio.create_task(self._track_position()),
            asyncio.create_task(self._track_armed()),
            asyncio.create_task(self._track_in_air()),
            asyncio.create_task(self._track_heading()),
            asyncio.create_task(self._track_distance()),
            asyncio.create_task(self._track_rc()),
            asyncio.create_task(self._track_flight_mode()),
        ]
        log.info("connected home=%s,%s", self.home_lat, self.home_lon)

    async def _wait_global_position(self) -> None:
        """Block until EKF reports global + home position, then store home."""
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                break
        async for pos in self.drone.telemetry.position():
            self.home_lat = pos.latitude_deg
            self.home_lon = pos.longitude_deg
            self._telem.lat = pos.latitude_deg
            self._telem.lon = pos.longitude_deg
            self._telem.relative_alt_m = pos.relative_altitude_m
            break

    async def _fire_failsafe(self, kind: str) -> None:
        """Notify ``Mission._on_failsafe`` (pump off). ``kind`` is a PumpOffEvent type."""
        if self.on_failsafe:
            await self.on_failsafe(kind)

    async def _track_rc(self) -> None:
        """If RC was seen then disappears, fire ``rc_loss``."""
        async for rc in self.drone.telemetry.rc_status():
            if rc.was_available_once:
                self._rc_seen = True
            self._telem.rc_available = rc.is_available
            if self._rc_seen and not rc.is_available:
                await self._fire_failsafe("rc_loss")

    async def _track_flight_mode(self) -> None:
        """After Offboard has been seen, leaving it (except RTL/land/hold) is ``offboard_loss``."""
        async for mode in self.drone.telemetry.flight_mode():
            self._telem.flight_mode = mode.name
            if mode == FlightMode.OFFBOARD:
                self._saw_offboard = True
            elif self._saw_offboard and mode not in {
                FlightMode.OFFBOARD,
                FlightMode.RETURN_TO_LAUNCH,
                FlightMode.LAND,
                FlightMode.HOLD,
            }:
                await self._fire_failsafe("offboard_loss")

    async def _track_position(self) -> None:
        """Update lat/lon/relative altitude from GLOBAL_POSITION."""
        async for pos in self.drone.telemetry.position():
            self._telem.lat = pos.latitude_deg
            self._telem.lon = pos.longitude_deg
            self._telem.relative_alt_m = pos.relative_altitude_m

    async def _track_armed(self) -> None:
        """Update ``telemetry.armed``."""
        async for armed in self.drone.telemetry.armed():
            self._telem.armed = armed

    async def _track_in_air(self) -> None:
        """Update ``telemetry.in_air`` (used for RC-first takeoff)."""
        async for in_air in self.drone.telemetry.in_air():
            self._telem.in_air = in_air

    async def _track_heading(self) -> None:
        """Update ``telemetry.heading_deg``."""
        async for att in self.drone.telemetry.heading():
            self._telem.heading_deg = att.heading_deg

    async def _track_distance(self) -> None:
        """Subscribe to DISTANCE_SENSOR. SIH typically never publishes; stay missing."""
        try:
            async for dist in self.drone.telemetry.distance_sensor():
                parsed = distance_reading_m(getattr(dist, "current_distance_m", None))
                if parsed is None:
                    self._telem.distance_sensor_missing = True
                    self._telem.distance_sensor_m = None
                else:
                    self._telem.distance_sensor_missing = False
                    self._telem.distance_sensor_m = parsed
        except Exception as exc:  # noqa: BLE001  SIH has no lidar
            log.info("distance_sensor unavailable: %s", exc)
            self._telem.distance_sensor_missing = True

    async def upload_fence(self, box: FenceBox) -> None:
        """Upload a PX4 inclusion polygon from the typed NED box."""
        if self.home_lat is None or self.home_lon is None:
            raise RuntimeError("no home position")
        corners = fence_corners_latlon(self.home_lat, self.home_lon, box)
        points = [Point(lat, lon) for lat, lon in corners]
        polygon = Polygon(points, FenceType.INCLUSION)
        await self.drone.geofence.upload_geofence(GeofenceData([polygon], []))

    async def wait_in_air(self, timeout_s: float = 60.0) -> None:
        """RC-first: block until PX4 reports in-air, else TimeoutError."""
        deadline = asyncio.get_event_loop().time() + timeout_s
        while asyncio.get_event_loop().time() < deadline:
            if self._telem.in_air:
                return
            await asyncio.sleep(0.25)
        raise TimeoutError("RC-first: vehicle not in air")

    async def arm_and_takeoff(self, agl_m: float) -> None:
        """Dashboard-first: arm, takeoff, wait until ~70% of ``agl_m``."""
        await self.drone.action.set_takeoff_altitude(agl_m)
        await self.drone.action.arm()
        await self.drone.action.takeoff()
        for _ in range(40):
            alt = self._telem.relative_alt_m or 0.0
            if alt >= agl_m * 0.7:
                return
            await asyncio.sleep(0.5)
        raise TimeoutError("takeoff altitude not reached")

    async def start_offboard_hold(self, north: float, east: float, down: float) -> None:
        """Send one NED setpoint then start Offboard (MAVSDK keeps ≥2 Hz)."""
        sp = PositionNedYaw(north, east, down, 0.0)
        await self.drone.offboard.set_position_ned(sp)
        try:
            await self.drone.offboard.start()
        except OffboardError as exc:
            log.warning("offboard start: %s - retry", exc)
            await asyncio.sleep(0.2)
            await self.drone.offboard.set_position_ned(sp)
            await self.drone.offboard.start()

    async def goto_ned(self, north: float, east: float, down: float, settle_s: float = 2.0) -> None:
        """Command Offboard position. ``down`` is NED z (positive down). Sleeps ``settle_s``."""
        await self.drone.offboard.set_position_ned(PositionNedYaw(north, east, down, 0.0))
        await asyncio.sleep(settle_s)

    async def pulse_pump(self, duration_s: float) -> None:
        """ON for ``duration_s`` then OFF in ``finally`` (never leave the pump latched)."""
        try:
            await self.set_pump(settings.pump_on)
            await asyncio.sleep(duration_s)
        finally:
            await self.set_pump(settings.pump_off)

    async def set_pump(self, value: float) -> None:
        """MAVSDK ``set_actuator(1, value)`` on [-1, 1]. OFF is 0.0 (proposed)."""
        try:
            await self.drone.action.set_actuator(settings.pump_index, value)
        except ActionError as exc:
            log.error("set_actuator: %s", exc)
            raise
        self.pump_value = value

    async def pump_off(self, reason: str) -> PumpOffEvent:
        """Command actuator 0 and return a log row. ``reason`` is a PumpOffEvent.type."""
        await self.set_pump(settings.pump_off)
        return PumpOffEvent(type=reason)  # type: ignore[arg-type]

    async def rtl(self) -> None:
        """Stop Offboard if running, then PX4 return-to-launch."""
        try:
            await self.drone.offboard.stop()
        except OffboardError:
            pass
        await self.drone.action.return_to_launch()

    async def kill(self) -> PumpOffEvent:
        """Pump off, leave Offboard, Hold (or RTL if Hold fails)."""
        event = await self.pump_off("kill")
        try:
            await self.drone.offboard.stop()
        except OffboardError:
            pass
        try:
            await self.drone.action.hold()
        except ActionError:
            try:
                await self.drone.action.return_to_launch()
            except ActionError:
                pass
        return event
