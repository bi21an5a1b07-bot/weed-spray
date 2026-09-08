# HTTP API

Base URL in SITL: `http://127.0.0.1:8000`. The dashboard calls the same paths under `/api` (Vite proxy strips the prefix). JSON uses `"class"` (not `class_name`) for detections.

## Backend (`weed_spray.backend.main`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Process up, phase, RTSP/MAVSDK strings |
| GET | `/state` | Full `AppState` snapshot |
| GET | `/ws` | WebSocket: snapshot every 250 ms |
| POST | `/connect` | MAVSDK `udpin://0.0.0.0:14540` |
| POST | `/fence` | Body: `{north_m,south_m,east_m,west_m}` local meters |
| POST | `/scan` | Body: `{source: "dashboard"\|"rc"}` (default `dashboard` if omitted). Starts lawnmower |
| POST | `/detections/inject` | Body: `{detections:[{id,class,north_m,east_m,conf?}]}` |
| POST | `/confirm` | `{ids:[...]}` (listed ids only; empty confirms nothing) and/or `{decisions:[{detection_id, decision: "confirm"\|"reject"}]}` |
| POST | `/visit` | Visit confirmed ids only; pulse; RTL |
| POST | `/rtl` | Pump off, return to launch |
| POST | `/kill` | Pump off, Hold (RTL if Hold fails) |
| POST | `/hold-people` | Pump off, hold (people/pets) |
| GET | `/run-log` | `sitl_template.md` JSON |
| GET | `/preflight` | FAA reminders (not compliance) |

Errors: backend `400` bad fence/ids/class, `409` mission already running, `503` connect failed. Vision unknown class on `POST /inject` → `422` (Pydantic).

Confirm is never implied by inject. A test harness may POST `/confirm`; the backend still requires that message.

## Vision (`weed_spray.vision.main`, `:8090`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | `mode=injector`, frozen `names` |
| GET | `/detections` | Current boxes |
| POST | `/inject` | Same detection schema; unknown class → `422` |
| DELETE | `/detections` | Clear |

SITL injects into **both** backend and vision (best-effort). If vision is down, backend still keeps detections.
