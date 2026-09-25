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
        scan_agl_m: Lawnmower altitude in metres (not spray hover).
        hover_agl_m: Commanded spray hover (S500/gz x500 gear ~0.22 m + ~2 in).
            NED down = -this when mode is ned.
        hover_altitude_mode: ``ned`` (default SIH) or ``offboard_agl``
            (MAVSDK PositionGlobalYaw.AltitudeType.AGL / PX4
            MAV_FRAME_GLOBAL_TERRAIN_ALT_INT; Gazebo lidar candidate).
        lidar_expected: Explicit belly-lidar / Gazebo capability flag.
            Default False (SIH). Required True with offboard_agl — SIH
            cannot fake this; flat Gazebo sets WEED_LIDAR_EXPECTED=1.
            False logs the hover sample as missing even when a short
            DISTANCE_SENSOR reading is present. The ned path still pulses.
        takeoff_timeout_s: Dashboard-first wait for relative_alt ≥ 70% of
            scan height (issue #27). Default 20 s (SIH). Gazebo needs 60-90.
        hover_min_m / hover_max_m: Accept band for measured AGL (above gear).
        lidar_mount_down_m: Belly lidar below CG (gz overlay z=-0.28).
            NED hover down = -(hover_agl_m + this) so the *lidar* is at hover_agl_m.
        pump_index: MAVSDK 1-based actuator index (Actuator Set 1).
        pump_on / pump_off: Scale [-1, 1]; OFF 0.0 is proposed.
        pump_pulse_s: App sleep around set_actuator, not a PX4 dwell.
        lawnmower_spacing_m: Row spacing along local east.
        scan_speed_m_s: Reserved; path currently uses settle sleeps.
        yolo_georeference: During scan, project vision pixels into local NED.
            Default false. Requires ``cam_hfov_deg`` and ``distance_scan_m``.
        cam_hfov_deg: Horizontal field of view in degrees. Unset refuses
            georeference. Do not invent a lens. Gazebo ``mono_cam`` in
            ``px4io/px4-sitl-gazebo`` is 1.74 rad (99.7°); that is a citation,
            not a default.
        cam_tilt_deg: Depression of the scan camera below the horizon.
            Unset refuses georeference. 90 is nadir. The Gazebo overlay uses 15.
        arrival_tolerance_m: Horizontal metres. Hover descent waits until the
            vehicle is this close to the ground point when tilt is below 80°.
        closing_speed_min_m_s: Slower than this toward the plant is not an approach.
        yolo_assoc_m: Same-class match radius in metres.
        yolo_conf: Drop pixel rows below this confidence.
        yolo_imgsz: Inference size used for the 20 px short-side rule.
    """

    model_config = SettingsConfigDict(env_prefix="WEED_", extra="ignore")

    mavsdk_address: str = "udpin://0.0.0.0:14540"
    rtsp_url: str = "rtsp://127.0.0.1:8554/cam"
    webrtc_url: str = "/cam/"
    vision_url: str = "http://127.0.0.1:8090"
    http_host: str = "127.0.0.1"
    http_port: int = 8000
    scan_agl_m: float = 2.0
    hover_agl_m: float = 0.27
    hover_altitude_mode: str = "ned"
    lidar_expected: bool = False
    takeoff_timeout_s: float = 20.0
    hover_min_m: float = 0.24
    hover_max_m: float = 0.32
    lidar_mount_down_m: float = 0.0
    pump_index: int = 1
    pump_on: float = 1.0
    pump_off: float = 0.0
    pump_pulse_s: float = 0.75
    lawnmower_spacing_m: float = 4.0
    scan_speed_m_s: float = 2.0
    yolo_georeference: bool = False
    cam_hfov_deg: float | None = None
    cam_tilt_deg: float | None = None
    arrival_tolerance_m: float = 0.5
    closing_speed_min_m_s: float = 0.2
    yolo_assoc_m: float = 0.35
    yolo_conf: float = 0.5
    yolo_imgsz: int = 640


settings = Settings()
"""Process-wide settings instance imported by vehicle, mission, and FastAPI."""
