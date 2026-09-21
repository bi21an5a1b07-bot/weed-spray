# Environment

Prefix `WEED_`. Defined in `weed_spray.backend.config.Settings`.

| Variable | Default | Meaning |
|---|---|---|
| `WEED_MAVSDK_ADDRESS` | `udpin://0.0.0.0:14540` | PX4 offboard listen address |
| `WEED_RTSP_URL` | `rtsp://127.0.0.1:8554/cam` | Camera URL (file in SITL, Pi later) |
| `WEED_WEBRTC_URL` | `/cam/` | Same-origin camera path (Vite proxies to MediaMTX `:8889`) |
| `WEED_VISION_URL` | `http://127.0.0.1:8090` | Injector |
| `WEED_HTTP_HOST` | `127.0.0.1` | Backend bind |
| `WEED_HTTP_PORT` | `8000` | Backend port |
| `WEED_SCAN_AGL_M` | `2.0` | Lawnmower altitude |
| `WEED_HOVER_AGL_M` | `0.27` | Commanded spray hover (gear ~0.22 m + ~2 in). Under `ned`, NED down = −this; under `offboard_agl`, **positive AGL metres** |
| `WEED_LIDAR_EXPECTED` | `false` | Belly-lidar / Gazebo capability. Required `true` with `offboard_agl`. Default SIH stays false (SIH cannot fake a real lidar) |
| `WEED_TAKEOFF_TIMEOUT_S` | `20` | Dashboard-first wait for relative_alt ≥ 70% of scan height (issue #27). SIH default 20 s; `make backend-gz` uses 90 |
| `WEED_HOVER_ALTITUDE_MODE` | `ned` | `ned` or `offboard_agl` (needs `WEED_LIDAR_EXPECTED`; latch scan-height stream → NED → in-band → AGL). Flat ds≈rel unlocks stream; lag/None-rel do not |
| `WEED_HOVER_MIN_M` / `MAX` | `0.24` / `0.32` | Accept band for measured AGL (above landing gear) |
| `WEED_LIDAR_MOUNT_DOWN_M` | `0.0` | Belly lidar below CG (metres). NED hover down = `-(hover_agl_m + this)` so lidar, not CG, is at hover AGL |
| `WEED_PUMP_INDEX` | `1` | MAVSDK actuator index (1-based = Set 1) |
| `WEED_PUMP_ON` / `OFF` | `1.0` / `0.0` | Scale [-1, 1]; OFF=0 is proposed |
| `WEED_PUMP_PULSE_S` | `0.75` | App sleep, not a PX4 dwell |
| `WEED_LAWNMOWER_SPACING_M` | `4.0` | Row spacing in local east |
| `WEED_SCAN_SPEED_M_S` | `2.0` | Reserved; path currently uses settle sleeps |

Unknown PX4 enums (`COM_OF_LOSS_T`, Kakute MAIN vs AUX, DIS/FAIL µs) are **not** set from env. Operator/QGC owns those.
