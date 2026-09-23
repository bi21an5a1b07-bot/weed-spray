"""MAVSDK wrapper. PX4 listens for offboard APIs on UDP 14540 (we bind)."""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import Awaitable, Callable

from mavsdk import System
from mavsdk.action import ActionError
from mavsdk.geofence import FenceType, GeofenceData, Point, Polygon
from mavsdk.offboard import OffboardError, PositionGlobalYaw, PositionNedYaw
from mavsdk.telemetry import FlightMode

from .config import settings
from .geo import fence_corners_latlon
from .models import FenceBox, PumpOffEvent, Telemetry

FailsafeHandler = Callable[[str], Awaitable[None]]

log = logging.getLogger("weed_spray.vehicle")


def ned_down_for_lidar_band(
    current_down: float, lidar_m: float, min_m: float, max_m: float
) -> float:
    """Shift NED ``down`` so lidar AGL moves toward the midpoint of ``[min_m, max_m]``.

    NED z is positive down. If lidar is too high (too many metres AGL), increase
    ``down`` (descend). If too low, decrease ``down`` (climb). Does not invent AGL.

    Args:
        current_down: Current Offboard NED down (negative = above origin).
        lidar_m: Trusted DISTANCE_SENSOR metres.
        min_m / max_m: Inclusive accept band.

    Returns:
        New NED down command.
    """
    target = (min_m + max_m) / 2.0
    return current_down + (lidar_m - target)


def should_nudge_for_lidar_band(
    lidar_m: float,
    min_m: float,
    max_m: float,
    last_nudged_lidar_m: float | None,
    *,
    change_eps_m: float = 0.02,
) -> bool:
    """Whether to apply ``ned_down_for_lidar_band`` for this poll.

    One nudge then wait. Re-applying ``down + (lidar - midpoint)`` on an
    already-nudged ``down`` when lidar changes (partial descent / noise)
    walks Offboard NED through the band into the ground or sky (PR #34).

    ``change_eps_m`` is unused; kept so callers that passed it still type-check.
    """
    _ = change_eps_m
    if min_m <= lidar_m <= max_m:
        return False
    return last_nudged_lidar_m is None


def _parse_distance_m(current: object) -> float | None:
    """Float metres or None for NaN / non-positive / junk."""
    if current is None:
        return None
    try:
        value = float(current)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or value <= 0:
        return None
    return value


def is_relative_alt_mirror(
    value_m: float,
    relative_alt_m: float | None,
    *,
    mirror_eps_m: float = 0.5,
    mirror_min_m: float = 1.0,
) -> bool:
    """True when a reading looks like SIH mirroring ``relative_alt_m`` (issue #12)."""
    if relative_alt_m is None or value_m < mirror_min_m:
        return False
    try:
        rel = float(relative_alt_m)
    except (TypeError, ValueError):
        return False
    if math.isnan(rel):
        return False
    return abs(value_m - rel) <= mirror_eps_m


def distance_reading_m(
    current: object,
    relative_alt_m: float | None = None,
    *,
    mirror_eps_m: float = 0.5,
    mirror_min_m: float = 1.0,
    max_trust_m: float = 1.0,
) -> float | None:
    """Parse trusted short-range lidar metres. NaN / non-positive / missing → None.

    This project only trusts short-range downward lidar for spray hover
    (about 0.24-0.32 m). Readings at or above ``max_trust_m`` (default 1 m)
    are treated as missing so SIH bogus streams (often ~relative alt, or a
    high value while commanded low) cannot pretend to be AGL (issue #12).

    Also drop SIH relative-alt mirrors (see ``is_relative_alt_mirror``). Low
    hover stays kept even if it matches relative_alt (real lidar can).
    """
    value = _parse_distance_m(current)
    if value is None:
        return None
    if value >= max_trust_m:
        return None
    if is_relative_alt_mirror(
        value, relative_alt_m, mirror_eps_m=mirror_eps_m, mirror_min_m=mirror_min_m
    ):
        return None
    return value


def apply_distance_sample(
    telem: Telemetry,
    current: object,
    relative_alt_m: float | None = None,
    *,
    stream_max_m: float = 5.0,
    stream_min_m: float = 1.0,
) -> None:
    """Update ``telem`` from one DISTANCE_SENSOR sample.

    Short-range trust (``distance_sensor_m``) is unchanged (#12).

    ``distance_sensor_stream_alive`` marks a contemporaneous scan-height sample
    (ds and relative_alt both in ``[stream_min_m, stream_max_m]``). Fail closed
    when ``relative_alt_m`` is None or still near hover while ds reads scan
    (lag unlock). Does **not** treat ds≈relative_alt as SIH-only — flat Gazebo
    belly lidar agrees with relative_alt too. SIH refuse is ``WEED_LIDAR_EXPECTED``.
    """
    parsed = distance_reading_m(current, relative_alt_m)
    if parsed is None:
        telem.distance_sensor_missing = True
        telem.distance_sensor_m = None
    else:
        telem.distance_sensor_missing = False
        telem.distance_sensor_m = parsed

    value = _parse_distance_m(current)
    if value is None or relative_alt_m is None:
        return
    try:
        rel = float(relative_alt_m)
    except (TypeError, ValueError):
        return
    if math.isnan(rel):
        return
    if stream_min_m <= value <= stream_max_m and stream_min_m <= rel <= stream_max_m:
        telem.distance_sensor_stream_alive = True


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
        """Subscribe to DISTANCE_SENSOR; SIH mirrors never mark stream alive."""
        try:
            async for dist in self.drone.telemetry.distance_sensor():
                apply_distance_sample(
                    self._telem,
                    getattr(dist, "current_distance_m", None),
                    self._telem.relative_alt_m,
                )
        except Exception as exc:  # noqa: BLE001  SIH has no lidar
            log.info("distance_sensor unavailable: %s", exc)
            self._telem.distance_sensor_missing = True
            self._telem.distance_sensor_stream_alive = False

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

    async def arm_and_takeoff(self, agl_m: float, timeout_s: float | None = None) -> None:
        """Dashboard-first: arm, takeoff, wait until ~70% of ``agl_m``.

        ``timeout_s`` defaults to ``settings.takeoff_timeout_s`` (20 s SIH).
        Gazebo climb is slower — set ``WEED_TAKEOFF_TIMEOUT_S`` (issue #27).
        ``relative_alt_m`` here is only “did takeoff climb?”, not spray AGL.
        """
        await self.drone.action.set_takeoff_altitude(agl_m)
        await self.drone.action.arm()
        await self.drone.action.takeoff()
        await self._wait_takeoff_alt(agl_m, timeout_s=timeout_s)

    async def _wait_takeoff_alt(self, agl_m: float, timeout_s: float | None = None) -> None:
        """Poll ``relative_alt_m`` until ≥ 70% of ``agl_m`` or ``TimeoutError``."""
        limit = settings.takeoff_timeout_s if timeout_s is None else timeout_s
        deadline = asyncio.get_event_loop().time() + limit
        target = agl_m * 0.7
        while asyncio.get_event_loop().time() < deadline:
            alt = self._telem.relative_alt_m or 0.0
            if alt >= target:
                return
            await asyncio.sleep(0.25)
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

    async def wait_lidar_hover_band(
        self,
        min_m: float,
        max_m: float,
        timeout_s: float = 15.0,
        north: float | None = None,
        east: float | None = None,
        down: float | None = None,
    ) -> float:
        """Poll trusted DISTANCE_SENSOR until it is in ``[min_m, max_m]``.

        Proof is lidar, not local ``z`` / relative_alt. Timeout does not invent AGL.
        Optional NED is re-sent so Offboard keeps the descend setpoint.
        At most one lidar-error NED nudge per wait; then hold that setpoint
        until in-band or timeout (partial descent must not restack error).

        Args:
            min_m: Inclusive lower accept band (metres AGL).
            max_m: Inclusive upper accept band (metres AGL).
            timeout_s: Wall-clock deadline.
            north, east, down: If all set, re-send this Offboard NED each poll.

        Returns:
            The in-band lidar metres.

        Raises:
            TimeoutError: Deadline hit; message includes last lidar and relative_alt.
        """
        deadline = asyncio.get_event_loop().time() + timeout_s
        last: float | None = None
        last_nudged_lidar: float | None = None
        while asyncio.get_event_loop().time() < deadline:
            if north is not None and east is not None and down is not None:
                await self.drone.offboard.set_position_ned(PositionNedYaw(north, east, down, 0.0))
            telem = self.telemetry
            last = telem.distance_sensor_m
            if last is not None and not telem.distance_sensor_missing and min_m <= last <= max_m:
                return last
            if (
                last is not None
                and not telem.distance_sensor_missing
                and down is not None
                and north is not None
                and east is not None
                and should_nudge_for_lidar_band(last, min_m, max_m, last_nudged_lidar)
            ):
                down = ned_down_for_lidar_band(down, last, min_m, max_m)
                last_nudged_lidar = last
            await asyncio.sleep(0.25)
        rel = self.telemetry.relative_alt_m
        raise TimeoutError(f"hover AGL not in band (lidar={last} rel={rel})")

    async def goto_global_agl(
        self, lat_deg: float, lon_deg: float, agl_m: float, settle_s: float = 2.0
    ) -> None:
        """Offboard global AGL hover via MAVSDK ``AltitudeType.AGL``.

        Maps to PX4 ``MAV_FRAME_GLOBAL_TERRAIN_ALT_INT`` (docs.px4.io Offboard).
        No PX4 params are written here — terrain/rangefinder fusion must already
        be live on the airframe (Gazebo ``gz_x500_lidar_down`` candidate).
        """
        sp = PositionGlobalYaw(
            lat_deg,
            lon_deg,
            agl_m,
            0.0,
            PositionGlobalYaw.AltitudeType.AGL,
        )
        await self.drone.offboard.set_position_global(sp)
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
