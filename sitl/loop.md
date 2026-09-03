# weed-spray SITL acceptance loop

Written 2026-08-30. Cloud-only note: this file is a contract. Do not start Docker from the Grok Bot VM. The sim host is the operator WSL2 DevStation (`/home/behmann/src/grok/drone_control`). Pump/Offboard notes: `px4/actuators.md`, `px4/offboard.md`.

Sources: `/workspace/weed-spray/PROJECT.md`, `SAFETY.md`, [PX4 Simulation](https://docs.px4.io/main/en/simulation/), [pre-built SITL packages](https://docs.px4.io/main/en/simulation/px4_sitl_prebuilt_packages), [SIH vs Gazebo](https://docs.px4.io/main/en/simulation/#simulator-comparison).

## What “green” means

Every process below is up. MAVSDK is connected on **UDP 14540**. Mock RTSP serves a **file**, not `/dev/video` and not a Gazebo camera. The dashboard loads. The YOLO worker is alive (or the injector is armed). Then the pass/fail script completes with **pump off on kill**.

No USB. No serial. No real radio. No real pump.

## Processes

Prefer the lightest PX4 SITL that can take Offboard. On ~25 GB RAM, Gazebo + YOLO is tight. Default PX4 is **SIH** (`px4io/px4-sitl`, `PX4_SIM_MODEL=sihsim_quadx`). SIH has IMU/GPS/baro/mag, not lidar or optical flow ([comparison](https://docs.px4.io/main/en/simulation/#simulator-comparison)). Hover AGL in this loop is therefore a **backend-recorded** number (commanded 0.15–0.30 m hold). `sitl/summaries/` will mark rangefinder `missing` unless Grok Build later adds Gazebo `gz_x500_lidar_down` ([rangefinders](https://docs.px4.io/main/en/sensor/rangefinders)).

| # | Process | Where | Image / binary | Role |
|---|---|---|---|---|
| 1 | PX4 SITL | Docker on WSL | `px4io/px4-sitl` (SIH). Compose file in the weed-spray repo only. | Flight stack. Offboard. Pump is a MAVLink actuator, not GPIO. |
| 2 | Mock RTSP | same compose or a repo helper | MediaMTX (or equivalent **in the repo compose**) + `ffmpeg` looping a lawn `.mp4` | v1 camera. File source. Not Gazebo RTP 5600. Not `/dev/video`. |
| 3 | Python backend | host, uv / Python 3.11 | weed-spray app | MAVSDK on 14540, geofence, scan, confirm, goto/hover, pump pulse, RTL, failsafe pump-off. |
| 4 | Dashboard | host | TypeScript web, localhost only | Typed geofence, confirm/reject, kill. No cloud. |
| 5 | YOLO worker | host, RTX 4090 | local detector | Boxes for `dandelion`, `clover`, `thistle`, `mallow`. Not a cloud LLM. Injector may stand in until weights exist. |

Do not add extra images at run time. If compose is missing, the run fails. Do not `apt install` or `docker pull` beyond that compose.

## Ports

| Port | Proto | Listener | Talks to |
|---|---|---|---|
| **14540** | UDP | backend MAVSDK | PX4 offboard. [PX4 remote API port](https://docs.px4.io/main/en/simulation/). Connect `udpin://0.0.0.0:14540`. |
| 14550 | UDP | optional QGC **inside WSL** | GCS. Not required for acceptance. |
| 8554 | TCP | mock RTSP | `rtsp://127.0.0.1:8554/cam` file loop. |
| **8000** | TCP | Python backend HTTP | Dashboard / injector API. |
| 8080 | TCP | dashboard | Localhost UI. |
| 8090 | TCP | injector (YOLO later) | Fake `dandelion`/`clover`/`thistle`/`mallow` boxes. |

PX4 also opens 8888/UDP (uXRCE-DDS) and SIH display 19410/UDP. Unused in v1. We do not run ROS.

WSL: use Docker `--network host` (or the compose equivalent) so 14540 lands on the host. One vehicle only.

## Pump

SITL pump = MAVLink **Peripheral via Actuator Set 1**. Laptop: MAVSDK `set_actuator(1, value)` / `MAV_CMD_DO_SET_ACTUATOR` param1, scaled [-1, 1]. Pulse **0.75 s** is app `asyncio.sleep`, not a PX4 dwell (`px4/actuators.md`). Default off (`set_actuator(1, 0)`). Forced off on kill, RC loss, laptop disconnect, geofence, Offboard loss. Extra pulses without a confirm are defects.

## Mock RTSP (file)

```text
rtsp://127.0.0.1:8554/cam
```

Operator drops a lawn clip into the repo (path TBD by Grok Build). `ffmpeg -re -stream_loop -1` publishes it. A `testsrc` clip is allowed only for connect-smoke, not for a green acceptance. Do not use Gazebo `gz_x500_mono_cam` RTP/5600 as the YOLO source. One ingest path, same URL the Pi will use later.

## Pass / fail script

Fill `/workspace/weed-spray/sitl/last-run.md` with these rows. `pass` / `fail` / `blocked`. First fail stops the grade (still write the remaining rows as `blocked`). Pump-off-on-kill is required even if an earlier step failed, if the vehicle was armed.

| Step | Action | Pass |
|---|---|---|
| 1 connect | Backend HEARTBEAT + MAVSDK on `udpin://0.0.0.0:14540` (also written `udp://:14540`). Dashboard loads. RTSP OPTIONS/DESCRIBE on `8554/cam` succeeds. Injector armed (YOLO later). | All four up. |
| 2 typed geofence box | Operator (or test harness) types a rectangle. Backend sets the fence. PX4 holds it. | Fence present in log (`geofence` corners). Outside is a breach. |
| 3 scan | Arm/takeoff per operator choice (RC-first or dashboard-first). Lawnmower scan at **2.0 m AGL** inside the box (`px4/offboard.md`, proposed). Do not scan at 6–12 in. | Path stays inside. Altitude is scan height, not spray hover. RC override still available. |
| 4 inject or detect boxes | Inject `dandelion` / `clover` / `thistle` / `mallow` with ids (`@weeds`: no trained YOLO yet). Live YOLO on the mock RTSP file is optional. | ≥1 detection with `id`, `class`, position. Fake boxes are a pass. |
| 5 confirm subset | Human (or harness acting as human) confirms a **subset**. Unconfirmed must not spray. | `confirms[]` exist. No pulse for unconfirmed ids. |
| 6 visit | Offboard goto XY at **scan height**, then descend. Do not dive to 6–12 in while translating. | Each confirmed id visited, none of the rejected. |
| 7 6–12 in hover | Hold 0.15–0.30 m AGL at the target. Record `hover_agl_m[]`. | Samples written. If no `distance_sensor`, write `missing` and **fail this step** (SIH has no lidar). Commanded hold still required. |
| 8 0.75 s pump pulse | One MAVLink actuator pulse per confirmed visit. | `pump_pulses[].duration_s` ≈ 0.75. Count = confirmed visits. Extra pulse = fail. |
| 9 RTL | RTL / land after the last confirmed target (or on operator RTL). | Vehicle RTLs. Pump off during RTL. |
| 10 pump-off on kill | Trigger kill: dashboard kill, or simulated RC loss / disconnect / fence exit. | Pump commanded off. `pump_off_events[]` or failsafe row with `pump_commanded_off=true`. **Required.** |

### Harness notes

- Confirm is never auto. A test harness may click confirm; the backend must still require that message.
- Injected boxes are the v1 pass (`@weeds`). Live YOLO on the file is later.
- Step 7 fails on SIH until rangefinder data exists. That is honest. Do not substitute `vehicle_local_position.z`.
- Speed: realtime (`PX4_SIM_SPEED_FACTOR` unset or 1). Faster-than-realtime is not acceptance.

## Start order (DevStation, operator-approved compose only)

1. Compose up PX4 SIH + mock RTSP (file).
2. YOLO worker (or injector).
3. Python backend (listens 14540, opens RTSP).
4. Dashboard.
5. Run the script above.
6. Compose down. Write `last-run.md`.

If Docker is not running or compose is missing: fail the run, write that in `last-run.md`, do not install anything.

## Nightly

A weekday 07:00 America/Denver routine exists and is **paused** until this script has one manual green pass. `compose.yaml` is already in the repo.

## Compose contract

Repo [`compose.yaml`](https://github.com/bi21an5a1b07-bot/weed-spray/blob/master/compose.yaml) on `master`. Do not start Docker from this Grok Bot VM.

| Piece | In compose.yaml |
|---|---|
| PX4 image | `px4io/px4-sitl:latest`, `PX4_SIM_MODEL=sihsim_quadx` ([pre-built SITL](https://docs.px4.io/main/en/simulation/px4_sitl_prebuilt_packages)) |
| Network | `network_mode: host` plus `host.docker.internal:127.0.0.1` so UDP **14540** stays on WSL, not Windows Docker Desktop |
| RTSP | MediaMTX + `mwader/static-ffmpeg` looping `media/smoke.mp4` to `rtsp://127.0.0.1:8554/cam` |
| backend HTTP | `8000` (host app, not this compose) |
| dashboard | `8080` (host app) |
| injector | `8090` (host app) |

## Open

| Item | Owner |
|---|---|
| One manual green pass, then unpause weekday 07:00 | operator |
| Hardware lidar UART | `@parts` / `@hardware` — not this loop |
