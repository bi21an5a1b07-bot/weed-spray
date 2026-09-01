# weed-spray

Laptop ground station for a backyard PX4 quad that spot-sprays dandelion, clover, and thistle. SITL first.

**Documentation:** [docs/README.md](docs/README.md) — architecture, API, SITL, vision, hardware, safety, testing, [function-level code reference](docs/code-reference.md), CLI, dashboard.

Grok Build instructions: [`GROK.md`](GROK.md).

SITL contract: [`bot_files/loop.md`](bot_files/loop.md) (downloaded from the Grok Bot VM). Product spec: [`agent_prompts/_shared/PROJECT.md`](agent_prompts/_shared/PROJECT.md).

## Layout

| Process | Port | How |
|---|---|---|
| PX4 SIH (`px4io/px4-sitl`, `sihsim_quadx`) | UDP 14540 offboard, 14550 GCS | `docker compose` |
| Mock RTSP (file, not Gazebo cam) | `rtsp://127.0.0.1:8554/cam` | MediaMTX + ffmpeg |
| Python backend | HTTP 8000 | MAVSDK, fence, scan, confirm, visit, pump, kill |
| Dashboard | HTTP 8080 | TypeScript, localhost only |
| Vision injector | HTTP 8090 | Injected boxes are the v1 pass |

No ROS. No cloud. Pump is MAVLink `set_actuator(1)`, 0.75 s pulse, off on kill.

## Run SITL (this WSL box)

```bash
uv sync
make sitl          # PX4 + RTSP. Needs Docker and ffmpeg for media/smoke.mp4
uv run weed-spray-vision &
uv run weed-spray &
(cd dashboard && npm install && npm run dev)
```

Browser: http://127.0.0.1:8080

Connect → set fence → inject happens via harness or `POST /api/detections/inject` → Scan → select detections → Confirm → Visit → Kill.

```bash
uv sync --extra dev
uv run pytest -q   # unit + integration (fake vehicle, no PX4)
make check         # ruff + pytest (Python gate)
make accept        # grades loop.md against live SITL; writes var/last-run.md
docker compose down
```

`media/smoke.mp4` is a `testsrc` clip for connect-smoke only. A real lawn `.mp4` is required for a green vision pass; injected boxes still pass step 4.

## Bot contracts (`bot_files/`)

Implemented against the 2026-08-30 Grok Bot files:

- Pump: `set_actuator(1)`, 0.75 s app pulse, `finally` off. Off on kill, RC loss, Offboard loss, RTL, people/pets hold.
- Offboard: `udpin://0.0.0.0:14540`, scan 2.0 m then XY-then-descend. **No invented PX4 params** (`COM_RCL_EXCEPT` bit 2 and `NAV_RCL_ACT=0` are not written).
- Run log: `GET /run-log` matches `sitl/summaries/_template.md`.
- Arm: dashboard-first or RC-first (`POST /scan` `{ "source": "rc"|"dashboard" }`).
- FAA: `GET /preflight` reminders only. Human confirm, geofence, kill stay in software.

Weed classes are frozen in `weeds/weeds.yaml` (`dandelion=0`, `clover=1`, `thistle=2`). SITL still uses the injector. Train later: `uv sync --extra yolo && uv run weed-spray-train` after you label `weeds/dataset/` or drop lawn photos in `weeds/inbox/`. Public archives are **not** auto-downloaded (`bot_files/weeds_sources.md`).

`$500` BOM does **not** close (`parts_cap.md`: ~$815). TFmini-S + PMW3901 kept. Companion is Pi 4 USB CDC (VBUS cut), not 14540 on the Kakute.

## Honest SIH limit

SIH has no downward lidar. Step 7 (6–12 in hover) **fails** unless `DISTANCE_SENSOR` is present. Commanded hold is still 0.15–0.30 m. Do not substitute `vehicle_local_position.z`. Gazebo `gz_x500_lidar_down` is a later compose profile, not v1.

## Safety

RC override is required on hardware. This SITL path sets PX4 params so the sim can arm without a transmitter. Never use those params on a real quad.
