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
| `WEED_LIDAR_MOUNT_DOWN_M` | `0.0` | Belly lidar below CG (metres). NED hover down = `-(hover_agl_m + this)` so lidar, not CG, is at hover AGL. Gazebo lidar tracks NED 1:1 — `make backend-gz` does **not** set 0.28 (that double-counted mount; see #33) |
| `WEED_PUMP_INDEX` | `1` | MAVSDK actuator index (1-based = Set 1) |
| `WEED_PUMP_ON` / `OFF` | `1.0` / `0.0` | Scale [-1, 1]; OFF=0 is proposed |
| `WEED_PUMP_PULSE_S` | `0.75` | App sleep, not a PX4 dwell |
| `WEED_LAWNMOWER_SPACING_M` | `4.0` | Row spacing in local east |
| `WEED_SCAN_SPEED_M_S` | `2.0` | Reserved; path currently uses settle sleeps |
| `WEED_YOLO_GEOREFERENCE` | `false` | During scan only, project vision pixels into unconfirmed `y*` rows. Off does not copy pixels into the mission |
| `WEED_CAM_HFOV_DEG` | unset | Horizontal FOV in degrees. Required when georeference is on. Unset skips the frame. Gazebo `mono_cam` in image `px4io/px4-sitl-gazebo` is **1.74 rad (99.7°)**, 1280×960 (`/opt/px4-gazebo/share/gz/models/mono_cam/model.sdf`). That citation is not a default. Do not copy the unit-test 90° |
| `WEED_CAM_TILT_DEG` | unset | Depression below the horizon. Unset skips georeference. 90 is straight down. The Gazebo overlay is **15** (pose pitch 0.2618 rad). Not a PX4 parameter |
| `WEED_ARRIVAL_TOLERANCE_M` | `0.5` | Hover descent waits until horizontal position is this close to the ground point when tilt is below 80°. Unset tilt or 90° does not add that wait |
| `WEED_CLOSING_SPEED_MIN_M_S` | `0.2` | Closing speed at or below this is not an approach. No arrival time is invented |
| `WEED_YOLO_ASSOC_M` | `0.35` | Same-class match radius in metres |
| `WEED_YOLO_CONF` | `0.5` | Drop pixel rows below this |
| `WEED_YOLO_IMGSZ` | `640` | Inference size for the 20 px short-side rule |

Unknown PX4 enums (`COM_OF_LOSS_T`, Kakute MAIN vs AUX, DIS/FAIL µs) are **not** set from env. Operator/QGC owns those.

## Vision worker

Read by `weed-spray-vision`, not by `Settings`.

| Variable | Default | Meaning |
|---|---|---|
| `WEED_YOLO_WEIGHTS` | empty | Empty → injector. A path that is not a file logs once and stays injector. A real file switches to `yolo`: without the `yolo` extra, `camera` is false and the box list is empty; with the extra, one RTSP reader starts. |
| `WEED_RTSP_URL` | `rtsp://127.0.0.1:8554/cam` | Same URL the backend uses. Read here only when a reader starts. |
| `WEED_YOLO_DEVICE` | `cpu` | Ultralytics device. Set `0` on the GPU. |
| `WEED_YOLO_CONF` | `0.5` | Detector floor inside the reader. The backend has its own `WEED_YOLO_CONF` for georeference. |
| `WEED_YOLO_IMGSZ` | `640` | Reader inference size. The backend has its own `WEED_YOLO_IMGSZ` for the 20 px rule. |
