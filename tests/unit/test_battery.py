"""PX4 pack voltage and remaining percent on telemetry. No live PX4."""

from types import SimpleNamespace

import pytest

from weed_spray.backend.models import Telemetry
from weed_spray.backend.vehicle import Vehicle, apply_battery_sample


def test_finite_pack_sample_is_stored():
    """MAVSDK remaining_percent is 0-100, so 1.0 is one percent."""
    telem = Telemetry()
    apply_battery_sample(telem, 16.4, 1.0)
    assert telem.battery_voltage_v == pytest.approx(16.4)
    assert telem.battery_remaining_pct == pytest.approx(1.0)


def test_invalid_sample_does_not_invent_or_clobber_a_pack():
    telem = Telemetry()
    apply_battery_sample(telem, None, None)
    apply_battery_sample(telem, float("nan"), 150)
    apply_battery_sample(telem, 0, -1)
    assert telem.battery_voltage_v is None
    assert telem.battery_remaining_pct is None

    apply_battery_sample(telem, 15.2, 40)
    apply_battery_sample(telem, float("nan"), 250)
    assert telem.battery_voltage_v == pytest.approx(15.2)
    assert telem.battery_remaining_pct == pytest.approx(40)


@pytest.mark.asyncio
async def test_battery_tracker_stores_voltage_and_percent():
    vehicle = Vehicle()

    async def samples():
        yield SimpleNamespace(voltage_v=15.8, remaining_percent=72.0)

    vehicle.drone = SimpleNamespace(telemetry=SimpleNamespace(battery=samples))
    await vehicle._track_battery()
    telem = vehicle.telemetry
    assert telem.battery_voltage_v == pytest.approx(15.8)
    assert telem.battery_remaining_pct == pytest.approx(72.0)
