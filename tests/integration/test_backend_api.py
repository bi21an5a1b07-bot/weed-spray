"""ASGI tests of the GCS FastAPI app with FakeVehicle (no MAVSDK, no PX4)."""

import asyncio

import httpx
import pytest

from tests.fakes import FakeVehicle
from weed_spray.backend import main as backend_main
from weed_spray.backend.mission import Mission


@pytest.fixture
async def api():
    """ASGI client bound to a Mission that uses FakeVehicle instead of MAVSDK."""
    fake = FakeVehicle()
    mission = Mission(fake)
    backend_main.vehicle = fake
    backend_main.mission = mission
    transport = httpx.ASGITransport(app=backend_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, mission, fake


@pytest.mark.asyncio
async def test_health_and_preflight(api):
    client, _, _ = api
    health = (await client.get("/health")).json()
    assert health["ok"] is True
    assert "14540" in health["mavsdk"]
    assert health["rtsp"].endswith(":8554/cam")
    pre = (await client.get("/preflight")).json()
    assert pre["not_legal_advice"] is True
    assert pre["human_confirm"] is True
    assert pre["part_137_open_before_real_spray"] is True
    assert pre["sitl_is_not_authorization"] is True


@pytest.mark.asyncio
async def test_connect_fence_inject_confirm_visit_kill(api):
    client, mission, fake = api
    assert (await client.post("/connect")).status_code == 200
    assert (
        await client.post(
            "/fence",
            json={"north_m": 20, "south_m": -5, "east_m": 15, "west_m": -15},
        )
    ).status_code == 200

    injected = await client.post(
        "/detections/inject",
        json={
            "detections": [
                {"id": "w1", "class": "dandelion", "north_m": 6, "east_m": 4},
                {"id": "w2", "class": "thistle", "north_m": 3, "east_m": 2},
            ]
        },
    )
    assert injected.status_code == 200
    assert {d["class"] for d in injected.json()["detections"]} == {
        "dandelion",
        "thistle",
    }

    scan = await client.post("/scan", json={"source": "dashboard"})
    assert scan.status_code == 200
    assert scan.json()["arm_source"] == "dashboard"
    await asyncio.wait_for(mission._run_task, timeout=2)
    state = (await client.get("/state")).json()
    assert state["phase"] == "awaiting_confirm"

    confirm = await client.post("/confirm", json={"ids": ["w1"]})
    assert confirm.status_code == 200
    assert confirm.json()["confirms"][0]["detection_id"] == "w1"

    visit = await client.post("/visit")
    assert visit.status_code == 200
    await asyncio.wait_for(mission._run_task, timeout=2)
    state = (await client.get("/state")).json()
    by_id = {d["id"]: d for d in state["detections"]}
    assert by_id["w1"]["sprayed"] is True
    assert by_id["w2"]["sprayed"] is False
    assert len(state["pump_pulses"]) == 1
    assert state["hover_agl_m"][0]["missing"] is True
    assert fake.pulses == 1

    log = (await client.get("/run-log")).json()
    assert log["geofence"]["n"] == 20
    assert log["confirms"][0]["decision"] == "confirm"
    assert log["pump_pulses"][0]["detection_id"] == "w1"

    killed = await client.post("/kill")
    assert killed.status_code == 200
    assert killed.json()["phase"] == "killed"
    assert any(e["pump_commanded_off"] for e in killed.json()["pump_off_events"])


@pytest.mark.asyncio
async def test_confirm_unknown_is_400(api):
    client, _, _ = api
    await client.post("/connect")
    rsp = await client.post("/confirm", json={"ids": ["ghost"]})
    assert rsp.status_code == 400


@pytest.mark.asyncio
async def test_hold_people(api):
    client, _, fake = api
    await client.post("/connect")
    rsp = await client.post("/hold-people")
    assert rsp.status_code == 200
    assert rsp.json()["phase"] == "killed"
    assert fake.pump_value == 0.0


@pytest.mark.asyncio
async def test_inject_bad_class_400(api):
    client, _, _ = api
    rsp = await client.post(
        "/detections/inject",
        json={"detections": [{"id": "x", "class": "crabgrass", "north_m": 0, "east_m": 0}]},
    )
    assert rsp.status_code == 400


@pytest.mark.asyncio
async def test_rc_first_scan(api):
    client, mission, fake = api
    await client.post("/connect")
    await client.post("/fence", json={"north_m": 8, "south_m": 0, "east_m": 8, "west_m": 0})
    await client.post("/scan", json={"source": "rc"})
    await asyncio.wait_for(mission._run_task, timeout=2)
    assert fake.waited_in_air == 1
    assert fake.armed_takeoff == 0
