"""FastAPI GCS on :8000. Route table: ``docs/api.md``."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .mission import Mission
from .models import ArmRequest, ConfirmRequest, FenceBox, InjectRequest
from .vehicle import Vehicle

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
log = logging.getLogger("weed_spray")

vehicle = Vehicle()
mission = Mission(vehicle)
_DEFAULT_ARM = ArmRequest()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """On shutdown, command the pump off even if a mission is mid-pulse."""
    yield
    try:
        await vehicle.pump_off("shutdown")
    except Exception as exc:  # noqa: BLE001  never block process exit
        log.warning("pump off on shutdown failed: %s", exc)


app = FastAPI(title="weed-spray", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Liveness plus current phase and configured RTSP/MAVSDK URLs."""
    return {
        "ok": True,
        "phase": mission.state.phase,
        "connected": vehicle.connected,
        "rtsp": settings.rtsp_url,
        "mavsdk": settings.mavsdk_address,
    }


@app.get("/state")
async def state():
    """Full AppState JSON (detections use key ``class``)."""
    return mission.snapshot().model_dump(mode="json", by_alias=True)


@app.post("/connect")
async def connect():
    """Bind MAVSDK to UDP 14540. 503 if PX4 is not sending."""
    try:
        await mission.connect()
    except Exception as exc:
        raise HTTPException(503, str(exc)) from exc
    return mission.snapshot().model_dump(mode="json", by_alias=True)


@app.post("/fence")
async def fence(box: FenceBox):
    """Upload a local-metre inclusion geofence."""
    try:
        await mission.set_fence(box)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return mission.snapshot().model_dump(mode="json", by_alias=True)


@app.post("/scan")
async def scan(arm: ArmRequest = _DEFAULT_ARM):
    """Start lawnmower scan. ``source=rc`` waits in-air; ``dashboard`` arms/takeoff."""
    try:
        await mission.start_scan(arm)
    except Exception as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"started": True, "phase": mission.state.phase, "arm_source": mission.state.arm_source}


@app.post("/detections/inject")
async def inject(req: InjectRequest):
    """Merge detections. Does not confirm or spray. Forwards to vision if up."""
    try:
        mission.inject(req)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            await client.post(
                f"{settings.vision_url}/inject",
                json=req.model_dump(by_alias=True),
            )
        except httpx.HTTPError:
            log.warning("vision worker unreachable; detections kept in backend")
    return mission.snapshot().model_dump(mode="json", by_alias=True)


@app.post("/confirm")
async def confirm(req: ConfirmRequest):
    """Human (or harness-as-human) confirm/reject. Required before /visit."""
    try:
        mission.confirm(req)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return mission.snapshot().model_dump(mode="json", by_alias=True)


@app.post("/visit")
async def visit():
    """Visit confirmed ids only: XY at 2 m, descend, pulse, RTL."""
    try:
        await mission.visit_now()
    except Exception as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"started": True, "phase": mission.state.phase}


@app.post("/rtl")
async def rtl():
    """Pump off and return to launch."""
    await mission.rtl()
    return mission.snapshot().model_dump(mode="json", by_alias=True)


@app.post("/kill")
async def kill():
    """Emergency: pump off, cancel mission task, Hold."""
    await mission.kill()
    return mission.snapshot().model_dump(mode="json", by_alias=True)


@app.post("/hold-people")
async def hold_people():
    """People/pets on the lawn: pump off and Hold."""
    await mission.hold_for_people()
    return mission.snapshot().model_dump(mode="json", by_alias=True)


@app.get("/run-log")
async def run_log():
    """sitl_template.md JSON for Grok Bot ``sitl`` or last-run export."""
    return mission.run_log()


@app.get("/preflight")
async def preflight():
    """bot_files/faa_current.md - reminders, not compliance."""
    return {
        "not_legal_advice": True,
        "rc_in_hand": True,
        "human_confirm": True,
        "vlos": True,
        "geofence_required": True,
        "pump_off_on_failsafe": True,
        "weigh_ready_to_fly_over_250g": True,
        "check_b4ufly": True,
        "part_137_open_before_real_spray": True,
        "sitl_is_not_authorization": True,
    }


@app.websocket("/ws")
async def ws(socket: WebSocket):
    """Push AppState every 250 ms until the client disconnects."""
    await socket.accept()
    try:
        while True:
            await socket.send_json(mission.snapshot().model_dump(mode="json", by_alias=True))
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return


def run() -> None:
    """CLI entry ``weed-spray``: uvicorn on WEED_HTTP_HOST:PORT."""
    uvicorn.run(
        "weed_spray.backend.main:app",
        host=settings.http_host,
        port=settings.http_port,
        reload=False,
    )


if __name__ == "__main__":
    run()
