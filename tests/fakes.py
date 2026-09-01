"""In-process stand-in for MAVSDK Vehicle. No PX4, no sleep."""

from __future__ import annotations

from types import SimpleNamespace

from weed_spray.backend.models import FenceBox, PumpOffEvent, Telemetry


class FakeVehicle:
    """Async stand-in for ``Vehicle``: no MAVSDK, no sleeps, records calls."""

    def __init__(self) -> None:
        """Recorded call lists start empty; lidar is missing like SIH."""
        self.connected = False
        self.pump_value = 0.0
        self.home_lat = 40.0
        self.home_lon = -105.0
        self.on_failsafe = None
        self.fence: FenceBox | None = None
        self.gotos: list[tuple[float, float, float]] = []
        self.pulses = 0
        self.armed_takeoff = 0
        self.waited_in_air = 0
        self.offboard_holds = 0
        self.rtl_calls = 0
        self.kills = 0
        self._telem = Telemetry(distance_sensor_missing=True)
        hold = _async_noop
        self.drone = SimpleNamespace(action=SimpleNamespace(hold=hold))

    @property
    def telemetry(self) -> Telemetry:
        """Same shape as ``Vehicle.telemetry``."""
        t = self._telem.model_copy()
        t.connected = self.connected
        t.pump_value = self.pump_value
        return t

    async def connect(self, address: str = "") -> None:
        """Mark connected; no UDP."""
        self.connected = True

    async def upload_fence(self, box: FenceBox) -> None:
        """Store the box; skip PX4 upload."""
        if self.home_lat is None:
            raise RuntimeError("no home position")
        self.fence = box

    async def wait_in_air(self, timeout_s: float = 60.0) -> None:
        """Immediate in-air (RC-first path)."""
        self.waited_in_air += 1
        self._telem.in_air = True
        self._telem.armed = True

    async def arm_and_takeoff(self, agl_m: float) -> None:
        """Count dashboard-first takeoffs; set relative altitude."""
        self.armed_takeoff += 1
        self._telem.in_air = True
        self._telem.armed = True
        self._telem.relative_alt_m = agl_m

    async def start_offboard_hold(self, north: float, east: float, down: float) -> None:
        """Record the hold setpoint."""
        self.offboard_holds += 1
        self.gotos.append((north, east, down))

    async def goto_ned(self, north: float, east: float, down: float, settle_s: float = 0.0) -> None:
        """Append NED without sleeping ``settle_s``."""
        self.gotos.append((north, east, down))

    async def pulse_pump(self, duration_s: float) -> None:
        """Count a pulse; leave pump at 0."""
        self.pulses += 1
        self.pump_value = 0.0

    async def set_pump(self, value: float) -> None:
        """Set the recorded actuator value."""
        self.pump_value = value

    async def pump_off(self, reason: str) -> PumpOffEvent:
        """Zero the pump and return a constructed off event."""
        self.pump_value = 0.0
        return PumpOffEvent.model_construct(type=reason, pump_commanded_off=True)

    async def rtl(self) -> None:
        """Count RTL."""
        self.rtl_calls += 1

    async def kill(self) -> PumpOffEvent:
        """Count kill and pump off."""
        self.kills += 1
        return await self.pump_off("kill")


async def _async_noop(*_a, **_k) -> None:
    """PX4 Hold no-op used by ``hold_for_people`` tests."""
    return
