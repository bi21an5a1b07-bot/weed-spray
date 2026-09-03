# Architecture

```
Operator browser (:8080)
        │  /api  +  /ws
        │  iframe /cam/  (Vite → MediaMTX :8889)
        ▼
Python backend (:8000) ── MAVSDK UDP 14540 ──► PX4 SIH (Docker, host net)
        │                                         pump: set_actuator(1)
        ├── vision injector (:8090)
        └── RTSP pull (later YOLO)  rtsp://127.0.0.1:8554/cam
                                          ▲
                         ffmpeg loops media/*.mp4 → MediaMTX
                         HLS :8888  WebRTC :8889
```

Nothing in the app leaves localhost. There is no ROS and no cloud LLM in the inner loop.

## Processes (`compose.yaml` + host)

| Process | Where | Port |
|---|---|---|
| `px4io/px4-sitl` `sihsim_quadx` | Docker, `network_mode: host` | UDP 14540 offboard, 14550 GCS |
| MediaMTX | Docker | TCP 8554 RTSP, 8888 HLS, 8889 WebRTC |
| ffmpeg publisher | Docker | publishes `cam` |
| `weed-spray` | host, uv | HTTP 8000 |
| `weed-spray-vision` | host, uv | HTTP 8090 |
| Vite dashboard | host | HTTP 8080 (proxies `/api` and `/ws`) |

## Mission sequence

1. Typed geofence (local NED meters from home).
2. Arm/takeoff: **dashboard-first** or **RC-first** (already in air).
3. Lawnmower scan at **2.0 m** AGL. Do not scan at 6–12 in.
4. Detections: injector (v1) or future YOLO. Classes: dandelion, clover, thistle.
5. Operator confirms a **subset**. Unconfirmed ids never pulse the pump.
6. Per confirmed id: Offboard goto XY at scan height, then descend, hold 0.15–0.30 m, pulse 0.75 s, pump off, next.
7. RTL. Pump off.
8. Kill / people-pets / RC loss / Offboard loss: pump commanded off.

NED **z is down**. Hover setpoint is `down = -0.22` m from local origin; that is **not** measured AGL on SIH.

## Contracts

| File | Role |
|---|---|
| `bot_files/sitl_loop.md` / `loop.md` | Accept steps and ports |
| `bot_files/px4_actuators.md` | Pump mapping |
| `bot_files/px4_offboard.md` | Offboard sequence; params **not** to invent |
| `bot_files/sitl_template.md` | `GET /run-log` schema |
| `bot_files/weeds_class-map.md` | Frozen YOLO ids |
| `agent_prompts/_shared/PROJECT.md` | Product spec |

Grok Bot `/workspace` is a different disk. See wiki concept: Bot files only affect this repo after they are copied into `bot_files/`.

## Code map

| Concern | Module |
|---|---|
| Settings | `weed_spray.backend.config` |
| HTTP + WS | `weed_spray.backend.main` |
| FSM | `weed_spray.backend.mission.Mission` |
| MAVSDK | `weed_spray.backend.vehicle.Vehicle` |
| NED / lawnmower | `weed_spray.backend.geo` |
| Injector | `weed_spray.vision.main` |
| Frozen classes | `weed_spray.vision.classes` |
| Accept grade | `weed_spray.harness.accept` |
| UI | `dashboard/src/App.tsx` |

Full function list: [code-reference.md](code-reference.md).
