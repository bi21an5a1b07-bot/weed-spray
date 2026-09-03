"""Process settings. Override with ``WEED_*`` environment variables.

See ``docs/environment.md``.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Tunable GCS constants. Unknown PX4 enums are not set from here.

    Attributes:
        mavsdk_address: MAVSDK bind; PX4 sends offboard traffic to UDP 14540.
        rtsp_url: Camera URL (file loop in SITL, Pi later).
        webrtc_url: MediaMTX WebRTC reader for the dashboard (browsers cannot play RTSP).
        vision_url: Injector base URL.
        http_host / http_port: Backend bind.
        scan_agl_m: Lawnmower altitude in metres (not 6-12 in).
        hover_agl_m: Commanded spray hover; NED down = -this.
        hover_min_m / hover_max_m: Accept band for measured AGL.
        pump_index: MAVSDK 1-based actuator index (Actuator Set 1).
        pump_on / pump_off: Scale [-1, 1]; OFF 0.0 is proposed.
        pump_pulse_s: App sleep around set_actuator, not a PX4 dwell.
        lawnmower_spacing_m: Row spacing along local east.
        scan_speed_m_s: Reserved; path currently uses settle sleeps.
    """

    model_config = SettingsConfigDict(env_prefix="WEED_", extra="ignore")

    mavsdk_address: str = "udpin://0.0.0.0:14540"
    rtsp_url: str = "rtsp://127.0.0.1:8554/cam"
    webrtc_url: str = "/cam/"
    vision_url: str = "http://127.0.0.1:8090"
    http_host: str = "127.0.0.1"
    http_port: int = 8000
    scan_agl_m: float = 2.0
    hover_agl_m: float = 0.22
    hover_min_m: float = 0.15
    hover_max_m: float = 0.30
    pump_index: int = 1
    pump_on: float = 1.0
    pump_off: float = 0.0
    pump_pulse_s: float = 0.75
    lawnmower_spacing_m: float = 4.0
    scan_speed_m_s: float = 2.0


settings = Settings()
"""Process-wide settings instance imported by vehicle, mission, and FastAPI."""
