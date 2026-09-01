"""Pydantic models for HTTP bodies, telemetry, and the sitl_template run log."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


def utc_now() -> str:
    """UTC timestamp in ISO-8601 for log rows."""
    return datetime.now(UTC).isoformat()


class MissionPhase(StrEnum):
    """Internal mission FSM. Not identical to sitl_template phase names."""

    idle = "idle"
    connecting = "connecting"
    connected = "connected"
    fence_set = "fence_set"
    taking_off = "taking_off"
    scanning = "scanning"
    awaiting_confirm = "awaiting_confirm"
    visiting = "visiting"
    hovering = "hovering"
    spraying = "spraying"
    rtl = "rtl"
    land = "land"
    killed = "killed"
    error = "error"


# Internal MissionPhase → sitl_template.md phase[] names (scan / spray_hover / rtl / land).
EXPORT_PHASE = {
    MissionPhase.idle: "idle",
    MissionPhase.scanning: "scan",
    MissionPhase.hovering: "spray_hover",
    MissionPhase.spraying: "spray_hover",
    MissionPhase.rtl: "rtl",
    MissionPhase.land: "land",
    MissionPhase.killed: "land",
}


class FenceBox(BaseModel):
    """Local NED meters from home: north/south/east/west edges."""

    north_m: float = 20.0
    south_m: float = -5.0
    east_m: float = 15.0
    west_m: float = -15.0


class Detection(BaseModel):
    """One plant in local NED metres. JSON uses ``class``, not ``class_name``."""

    id: str
    class_name: str = Field(alias="class", serialization_alias="class")
    north_m: float
    east_m: float
    conf: float = 1.0
    confirmed: bool = False
    visited: bool = False
    sprayed: bool = False
    t: str = Field(default_factory=utc_now)

    model_config = {"populate_by_name": True}


class InjectRequest(BaseModel):
    """POST /detections/inject body."""

    detections: list[Detection]


class ConfirmDecision(BaseModel):
    """One confirm or reject. Inject never implies confirm."""

    detection_id: str
    decision: Literal["confirm", "reject"]


class ConfirmRequest(BaseModel):
    """POST /confirm. ``ids`` are treated as confirm; ``decisions`` may reject."""

    ids: list[str] = Field(default_factory=list)
    decisions: list[ConfirmDecision] = Field(default_factory=list)


class ArmRequest(BaseModel):
    """POST /scan: dashboard-first takeoff vs wait for RC-in-air."""

    source: Literal["rc", "dashboard"] = "dashboard"


class ConfirmEvent(BaseModel):
    """Logged confirm/reject row (sitl_template confirms[])."""

    t: str = Field(default_factory=utc_now)
    detection_id: str
    decision: Literal["confirm", "reject"]


class HoverSample(BaseModel):
    """One spray-hover AGL sample. ``missing`` if no DISTANCE_SENSOR (SIH)."""

    t: str = Field(default_factory=utc_now)
    detection_id: str
    agl_m: float | None = None
    missing: bool = False


class PumpPulse(BaseModel):
    """One commanded 0.75 s actuator pulse tied to a confirmed detection."""

    t: str = Field(default_factory=utc_now)
    duration_s: float
    detection_id: str
    commanded: bool = True


class PumpOffEvent(BaseModel):
    """Failsafe or operator pump-off. ``pump_commanded_off`` must be true."""

    t: str = Field(default_factory=utc_now)
    type: Literal[
        "kill",
        "rc_loss",
        "offboard_loss",
        "geofence",
        "disconnect",
        "rtl",
        "failsafe",
        "people",
        "mission_error",
        "shutdown",
    ]
    pump_commanded_off: bool = True


class PhaseEvent(BaseModel):
    """Exported phase timeline entry (``scan``, ``spray_hover``, ``rtl``, …)."""

    t: str = Field(default_factory=utc_now)
    name: str


class Telemetry(BaseModel):
    """Last MAVSDK snapshot. ``distance_sensor_missing`` is true on SIH."""

    connected: bool = False
    armed: bool = False
    in_air: bool = False
    lat: float | None = None
    lon: float | None = None
    relative_alt_m: float | None = None
    heading_deg: float | None = None
    distance_sensor_m: float | None = None
    distance_sensor_missing: bool = True
    pump_value: float = 0.0
    flight_mode: str | None = None
    rc_available: bool | None = None


class AppState(BaseModel):
    """Full GCS state returned by GET /state and the WebSocket."""

    phase: MissionPhase = MissionPhase.idle
    telemetry: Telemetry = Field(default_factory=Telemetry)
    fence: FenceBox | None = None
    detections: list[Detection] = Field(default_factory=list)
    confirms: list[ConfirmEvent] = Field(default_factory=list)
    last_error: str | None = None
    pump_pulses: list[PumpPulse] = Field(default_factory=list)
    pump_off_events: list[PumpOffEvent] = Field(default_factory=list)
    hover_agl_m: list[HoverSample] = Field(default_factory=list)
    phase_log: list[PhaseEvent] = Field(default_factory=list)
    rtsp_url: str = ""
    mavsdk_address: str = ""
    arm_source: Literal["rc", "dashboard"] | None = None
    t_start: str | None = None
    kind: Literal["sitl", "hw"] = "sitl"
