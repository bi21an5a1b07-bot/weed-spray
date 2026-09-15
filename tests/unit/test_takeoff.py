"""arm_and_takeoff altitude wait (issue #27). No live PX4."""

import asyncio

import pytest

from weed_spray.backend.vehicle import Vehicle


@pytest.mark.asyncio
async def test_wait_takeoff_alt_reaches_within_timeout():
    v = Vehicle()
    v._telem.relative_alt_m = 0.0

    async def climb() -> None:
        await asyncio.sleep(0.05)
        v._telem.relative_alt_m = 2.0

    task = asyncio.create_task(climb())
    await v._wait_takeoff_alt(2.0, timeout_s=1.0)
    await task


@pytest.mark.asyncio
async def test_wait_takeoff_alt_times_out():
    v = Vehicle()
    v._telem.relative_alt_m = 0.1
    with pytest.raises(TimeoutError, match="takeoff altitude not reached"):
        await v._wait_takeoff_alt(2.0, timeout_s=0.05)


def test_takeoff_timeout_setting_default_is_sih_20s():
    from weed_spray.backend.config import Settings

    assert Settings().takeoff_timeout_s == 20.0
