# GROK.md — weed-spray

Instructions for Grok Build in `/home/behmann/src/grok/drone_control`. This is a **personal hobby** backyard PX4 spot-spray GCS, not Axon work.

Product spec: [`agent_prompts/_shared/PROJECT.md`](agent_prompts/_shared/PROJECT.md). Safety: [`agent_prompts/_shared/SAFETY.md`](agent_prompts/_shared/SAFETY.md). How the code works: [`docs/README.md`](docs/README.md). Do not duplicate those files here; follow them.

## What this repo is

Laptop ground station for a US-hobby backyard quad. PX4 over MAVLink. Scan the lawn, human confirms weeds, then hover 6-12 in AGL and pulse a 12 V vinegar/salt pump. **SITL first** (Docker SIH on this WSL box). Hardware later.

Python 3.11 (uv) + TypeScript dashboard. **No ROS. No cloud in the inner loop.** Localhost/LAN only.

## Hard rules

**Never**

- Auto-confirm a spray. Inject is not confirm. Unconfirmed ids never pulse the pump.
- Arm, Offboard, or pulse a pump on **real** hardware from this agent unless the operator is on the RC and asked for that step.
- Invent PX4 parameters. Do not write `COM_RCL_EXCEPT` bit 2 or disable `NAV_RCL_ACT`. Unknown enums stay unknown ([`bot_files/px4_offboard.md`](bot_files/px4_offboard.md)).
- Treat GPS / `vehicle_local_position.z` as AGL. SIH has no `DISTANCE_SENSOR`; hover samples log `missing` and accept step 7 **fails**.
- Renumber YOLO classes or add a fourth class. Frozen: `dandelion=0`, `clover=1`, `thistle=2`. Turf/crabgrass/`other_weed` is unlabeled background.
- Auto-download public weed archives (licenses: CC-BY-NC, ShareAlike, custom NC).
- Drop TFmini-S or PMW3901 to hit the $500 cap. Report the dollar gap (`bot_files/parts_cap.md`, ~$815).
- Treat `GET /preflight` or SITL as FAA/Part 137 authorization. Not legal advice.
- Catch-and-pass around pump-off without logging.

**Always**

- Pump: `set_actuator(1)`, ON=1, OFF=0, 0.75 s app pulse, `finally` off. Off on kill, RC loss, Offboard loss, RTL, people/pets hold, shutdown.
- Scan at **2.0 m AGL**. Per confirmed id: XY at scan height, **then** descend to 0.15-0.30 m, pulse, climb, next.
- Offboard: bind `udpin://0.0.0.0:14540`. Setpoint **before** `offboard.start()`. NED z is down (`hover` down = `-0.22`).
- RC in the pilot's hands whenever motors can spin (hardware). SITL may be dashboard-first.
- Cite `bot_files/` when changing flight, pump, class map, or accept behavior.

## Grok Bot vs this workspace

Grok **Build** writes this git repo. Grok **Bot** VMs have a separate `/workspace`. Bot contracts only affect this tree after the operator copies them into [`bot_files/`](bot_files/). Do not assume Bot files are already here.

## Layout

| Path | Role |
|---|---|
| `src/weed_spray/backend/` | FastAPI GCS `:8000`, MAVSDK `Vehicle`, `Mission` FSM |
| `src/weed_spray/vision/` | Injector `:8090` + optional `weed-spray-train` |
| `src/weed_spray/harness/accept.py` | Live `loop.md` grader |
| `dashboard/src/` | Vite React UI `:8080` (`/api` and `/ws` proxied) |
| `tests/` | pytest + `FakeVehicle` — **no live PX4** |
| `compose.yaml` | PX4 SIH + MediaMTX + ffmpeg only |
| `bot_files/` | Normative Bot contracts |
| `docs/` | Human docs; [`docs/code-reference.md`](docs/code-reference.md) for functions |

## Commands

```bash
uv sync --extra dev
make sitl                 # PX4 SIH + RTSP file loop (Docker)
uv run weed-spray-vision  # :8090
uv run weed-spray         # :8000
(cd dashboard && npm run dev)  # :8080

make check                # ruff check + ruff format --check + pytest
make lint / make fmt
make accept               # live 10-step loop.md; needs SITL + apps
```

Python gate after every Python edit:

```bash
uv run ruff check --fix src tests
uv run ruff format src tests
uv run pytest -q
```

Ruff config is `[tool.ruff]` in `pyproject.toml`. Do not disable a rule to hide a bug; fix the code or add a targeted `# noqa: CODE` with a reason.

## Contracts (normative)

| File | Do not violate |
|---|---|
| `bot_files/loop.md` / `sitl_loop.md` | Ports and 10 accept steps |
| `bot_files/px4_actuators.md` | Actuator Set 1 = pump |
| `bot_files/px4_offboard.md` | Sequence; params not to invent |
| `bot_files/sitl_template.md` | `GET /run-log` JSON |
| `bot_files/weeds_class-map.md` | Frozen `nc=3` |

Compose images stay exactly: `px4io/px4-sitl` (`PX4_SIM_MODEL=sihsim_quadx`), `bluenviron/mediamtx`, `mwader/static-ffmpeg:7.1` (binary is `/ffmpeg`). `network_mode: host`. One vehicle.

## SITL vs hardware

- RTSP is a **file** loop (`rtsp://127.0.0.1:8554/cam`), not Gazebo RTP, not `/dev/video` (WSL has no USB camera).
- Injected boxes are the v1 detect pass. Live YOLO on RTSP is later, after labeled `weeds/dataset/`.
- Companion on hardware: Pi 4 USB CDC to Kakute H7 Mini, **VBUS cut**, not UDP 14540 on the Kakute. Maiden: pump lead **open**.

## Do not start unless asked

YOLO training, companion Pi image, live `weed-spray-accept` against PX4, wiki ingest, Gazebo lidar profile.

## Docs to open first

1. [`docs/README.md`](docs/README.md)
2. [`docs/architecture.md`](docs/architecture.md) / [`docs/safety.md`](docs/safety.md)
3. The `bot_files/` contract for the subsystem you are touching
