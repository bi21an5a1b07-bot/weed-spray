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
| `WEED_HOVER_AGL_M` | `0.22` | Commanded spray hover (NED down = −this) |
| `WEED_HOVER_MIN_M` / `MAX` | `0.15` / `0.30` | Accept band for measured AGL |
| `WEED_PUMP_INDEX` | `1` | MAVSDK actuator index (1-based = Set 1) |
| `WEED_PUMP_ON` / `OFF` | `1.0` / `0.0` | Scale [-1, 1]; OFF=0 is proposed |
| `WEED_PUMP_PULSE_S` | `0.75` | App sleep, not a PX4 dwell |
| `WEED_LAWNMOWER_SPACING_M` | `4.0` | Row spacing in local east |

Unknown PX4 enums (`COM_OF_LOSS_T`, Kakute MAIN vs AUX, DIS/FAIL µs) are **not** set from env. Operator/QGC owns those.
