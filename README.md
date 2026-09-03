# weed-spray

## Proof of concept / vibe code solution.  Do not trust it.

Laptop ground station for a US-hobby backyard PX4 quad. The drone lawnmower-scans a typed geofence, the operator confirms weeds on a localhost dashboard, then the vehicle visits each confirmed plant, holds 6–12 inches AGL, and pulses a 12 V household vinegar/salt pump.

**SITL first.** Hardware comes later. There is no ROS and no cloud in the inner loop.

| | Detail |
|---|---|
| Stack | Python 3.11 (FastAPI + MAVSDK) and a TypeScript dashboard |
| Flight | PX4 Offboard over MAVLink (`udpin://0.0.0.0:14540`) |
| Sim | Docker SIH (`px4io/px4-sitl`, `sihsim_quadx`) + file RTSP |
| Classes | `dandelion`, `clover`, `thistle`, `mallow` (mallow includes ground ivy) |
| Pump | MAVLink `set_actuator(1)`, 0.75 s pulse, off on every failsafe |

Product spec: [`agent_prompts/_shared/PROJECT.md`](agent_prompts/_shared/PROJECT.md). How the code works: [`docs/README.md`](docs/README.md). Agent rules: [`GROK.md`](GROK.md).

## Status

| Piece | Now | Later |
|---|---|---|
| Flight loop | SITL Offboard scan → confirm → visit → RTL | Real Kakute + Pi 4 USB CDC |
| Detections | Injected boxes (`weed-spray-vision`) | Live YOLO on RTSP after labeled `weeds/dataset/` |
| Hover AGL | Commanded 0.15–0.30 m; SIH has **no lidar** | TFmini-S `DISTANCE_SENSOR` (Gazebo profile is not v1) |
| Camera | Looped `media/*.mp4` on `rtsp://127.0.0.1:8554/cam` | Pi WiFi RTSP, same URL |
| BOM | ~$815 all-in vs a $500 cap; TFmini-S and PMW3901 stay | Do not drop rangefinder or flow to close the gap |

Accept step 7 (measured 6–12 in hover) **fails on SIH** unless a rangefinder is present. Do not treat GPS or `vehicle_local_position.z` as AGL.

## Safety

These are software rules, not a license to fly.

- **Human confirm before every spray.** Inject is not confirm. Unconfirmed ids never pulse the pump.
- **RC in the pilot's hands** whenever motors can spin on hardware. SITL may take off from the dashboard; that path must not be copied onto a real quad.
- Pump is commanded **off** on kill, people/pets hold, RC loss, Offboard loss, RTL, geofence, disconnect, and process shutdown.
- SITL may set PX4 params so the sim can arm without a transmitter. **Never use those params on hardware.**
- `GET /preflight` is a reminder list, not FAA or Part 137 authorization. Grocery vinegar from an aircraft is not documented as a free pass. See [`docs/safety.md`](docs/safety.md) and [`bot_files/faa_current.md`](bot_files/faa_current.md).

This software does not arm or pulse a real aircraft.

## Requirements

- Linux (developed on WSL2 Ubuntu) with [mise](https://mise.jdx.dev/walkthrough.html) and Docker
- Host `ffmpeg` (apt) for `make smoke-video`
- Optional NVIDIA GPU for YOLO training (`uv sync --extra yolo`)

mise pins **Python 3.11**, **uv**, and **Node 26**. Python packages live in `pyproject.toml` (`uv sync`). Dashboard packages live in `dashboard/` (`npm install`). Docker is a host daemon, not a mise tool.

## Quick start

```bash
mise trust && mise install && mise run install
make sitl                 # PX4 SIH + MediaMTX + ffmpeg file RTSP
uv run weed-spray-vision  # injector :8090
uv run weed-spray         # backend  :8000
(cd dashboard && npm run dev)  # UI :8080
```

Open http://127.0.0.1:8080

1. **Connect** — MAVSDK binds UDP 14540.
2. **Set fence** — north/south/east/west metres from home.
3. **Inject** detections (harness, or `POST /api/detections/inject`).
4. **Scan** — lawnmower at **2.0 m** AGL (dashboard-first in SITL, or RC-first if already in the air).
5. Select a **subset** of rows → **Confirm selected**.
6. **Visit confirmed** — XY at scan height, then descend, 0.75 s pulse, next, RTL.
7. **Kill (pump off)** or **People/pets — hold** at any time.

```bash
make down                 # docker compose down
```

`media/smoke.mp4` is an 8 s `testsrc` clip for connect-smoke. A real lawn `.mp4` is required for a green vision pass; injected boxes still pass detect-step 4.

More detail: [`docs/getting-started.md`](docs/getting-started.md).

## Architecture

```
Operator browser (:8080)
        │  /api  +  /ws
        │  HLS /hls/cam/  (Vite → MediaMTX :8888)
        ▼
Python backend (:8000) ── MAVSDK UDP 14540 ──► PX4 SIH (Docker, host net)
        │                                         pump: set_actuator(1)
        ├── vision injector (:8090)
        └── RTSP pull (later YOLO)  rtsp://127.0.0.1:8554/cam
                                          ▲
                         ffmpeg loops media/*.mp4 → MediaMTX
```

Nothing in the app leaves localhost.

| Process | Port | How |
|---|---|---|
| PX4 SIH (`px4io/px4-sitl`, `sihsim_quadx`) | UDP 14540 offboard, 14550 GCS | `make sitl` |
| Mock RTSP (file, not Gazebo cam) | `rtsp://127.0.0.1:8554/cam` | MediaMTX + ffmpeg |
| HLS / WebRTC | TCP 8888 / 8889 | dashboard plays HLS |
| Python backend | HTTP 8000 | MAVSDK, fence, scan, confirm, visit, pump, kill |
| Dashboard | HTTP 8080 | Vite; proxies `/api` and `/ws` |
| Vision injector | HTTP 8090 | Injected boxes are the v1 detect pass |

Compose starts **only** PX4, MediaMTX, and the ffmpeg publisher. Backend, vision, and dashboard stay on the host. Images are pinned in `compose.yaml`; do not add more at runtime.

Scan at 2.0 m, then per confirmed id: goto XY at scan height, **then** descend to 0.15–0.30 m, pulse, climb, next. NED **z is down** (`hover` down = `-0.22`). That commanded hold is not measured AGL on SIH.

## Vision

Frozen map (`weeds/weeds.yaml`, never renumber 0/1/2):

| id | name | Notes |
|---:|---|---|
| 0 | `dandelion` | *Taraxacum* |
| 1 | `clover` | *Trifolium*, not *Oxalis* |
| 2 | `thistle` | *Cirsium* / *Carduus* as one class |
| 3 | `mallow` | *Malva* + ground ivy (*Glechoma*) |

Turf, dirt, crabgrass, plantain, and “other weed” are unlabeled background. Public archives are **not** auto-downloaded.

Unlabeled intake lives in `weeds/inbox/` (iNat CC0/CC-BY stills plus 1 fps frames from `media/backyard_weeds.MOV`). Box those stills, then promote and train:

```bash
make inbox-frames                          # skip if frames exist
uv run python scripts/promote_inbox.py     # boxed inbox → dataset train/val
uv sync --extra yolo
uv run weed-spray-train --list-sources     # prints sources; never downloads
uv run weed-spray-train                    # refuses if dataset images are empty
```

SITL still uses the injector until live YOLO exists. Labeling rules: [`weeds/README.md`](weeds/README.md), [`docs/vision.md`](docs/vision.md).

## Hardware (not this path)

Target airframe is an S500 + Kakute H7 Mini + Pi 4 (USB CDC, **VBUS cut**) + TFmini-S + PMW3901 + 12 V CrocSee pump on actuator set 1. Companion is not UDP 14540 on the Kakute. Maiden: pump lead **open**.

This repo does not power, arm, or spray hardware. See [`docs/hardware.md`](docs/hardware.md).

## Development

```bash
uv sync --extra dev
uv run pytest -q          # unit + HTTP integration (FakeVehicle, no PX4)
make check                # ruff check + ruff format --check + pytest
make accept               # live 10-step loop.md grade; writes var/last-run.md
```

`make check` is the Python gate after every Python edit. Live accept needs SITL + backend + vision up; step 7 is expected to fail on SIH.

| Command | What |
|---|---|
| `uv run weed-spray` | GCS on `127.0.0.1:8000` |
| `uv run weed-spray-vision` | Injector on `:8090` |
| `uv run weed-spray-accept` | Grade `bot_files/loop.md` against a live sim |
| `make sitl` / `make down` | Compose up / down |
| `make lint` / `make fmt` | Ruff |

Settings use the `WEED_` prefix ([`docs/environment.md`](docs/environment.md)). Commands: [`docs/cli.md`](docs/cli.md). Tests: [`docs/testing.md`](docs/testing.md).

Normative contracts live in [`bot_files/`](bot_files/) (ports, pump mapping, Offboard sequence, class map, run-log schema). Do not invent PX4 parameters; `COM_RCL_EXCEPT` bit 2 and `NAV_RCL_ACT=0` are not written.

## Documentation

| Doc | Contents |
|---|---|
| [Getting started](docs/getting-started.md) | mise, install, SITL, dashboard, tests |
| [Architecture](docs/architecture.md) | Processes, ports, mission sequence |
| [HTTP API](docs/api.md) | Backend `:8000` and vision `:8090` |
| [SITL](docs/sitl.md) | Docker SIH, RTSP, accept script |
| [Vision](docs/vision.md) | Frozen classes, injector, training |
| [Hardware](docs/hardware.md) | Kakute / Pi / pump mapping |
| [Safety](docs/safety.md) | Confirm, RC, failsafes, FAA notes |
| [Testing](docs/testing.md) | Ruff, pytest, live `weed-spray-accept` |
| [Code reference](docs/code-reference.md) | Every module and function |
| [CLI and Makefile](docs/cli.md) | `uv run` entries and `make` targets |
| [Dashboard](docs/dashboard.md) | Vite UI on `:8080` |
| [Repository layout](docs/repository-layout.md) | Tree of the git repo |
| [Environment](docs/environment.md) | `WEED_*` settings |
