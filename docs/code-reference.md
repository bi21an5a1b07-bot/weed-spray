# Code reference

Function-level behavior for every module that implements the GCS, vision worker, accept harness, dashboard, and test doubles. Source of truth is the file; this page matches those docstrings.

Normative product rules still live in `bot_files/` and `agent_prompts/_shared/`. This page documents **code**.

---

## `src/weed_spray/__init__.py`

Package marker. No runtime API.

---

## `src/weed_spray/backend/config.py`

Process settings. Override with `WEED_*` environment variables (see [environment.md](environment.md)).

### `class Settings(BaseSettings)`

Pydantic settings. `env_prefix="WEED_"`, unknown env keys ignored. Does **not** write PX4 parameters.

| Field | Default | Meaning |
|---|---|---|
| `mavsdk_address` | `udpin://0.0.0.0:14540` | MAVSDK bind; PX4 sends offboard traffic here |
| `rtsp_url` | `rtsp://127.0.0.1:8554/cam` | Camera URL (file loop in SITL) |
| `webrtc_url` | `/cam/` | Same-origin camera path; Vite proxies to MediaMTX `:8889` |
| `vision_url` | `http://127.0.0.1:8090` | Injector base URL |
| `http_host` / `http_port` | `127.0.0.1` / `8000` | Backend bind |
| `scan_agl_m` | `2.0` | Lawnmower altitude (metres) |
| `hover_agl_m` | `0.27` | Commanded spray hover (gear ~0.22 m + ~2 in); NED down = `−this` when mode is `ned` |
| `hover_altitude_mode` | `ned` | `ned` (SIH) or `offboard_agl` (MAVSDK AGL / PX4 terrain-alt Offboard) |
| `lidar_expected` | `false` | Required `true` with `offboard_agl` (Gazebo); SIH stays false |
| `takeoff_timeout_s` | `20` | Dashboard-first wait for relative_alt ≥ 70% of scan height |
| `hover_min_m` / `hover_max_m` | `0.24` / `0.32` | Accept band for **measured** AGL (above landing gear) |
| `lidar_mount_down_m` | `0.0` | Belly lidar below CG; NED hover down = `-(hover_agl_m + this)` |
| `pump_index` | `1` | MAVSDK 1-based actuator index (Actuator Set 1) |
| `pump_on` / `pump_off` | `1.0` / `0.0` | Scale `[-1, 1]`; OFF `0` is proposed |
| `pump_pulse_s` | `0.75` | App sleep around `set_actuator`; not a PX4 dwell |
| `lawnmower_spacing_m` | `4.0` | Row spacing along local east |
| `scan_speed_m_s` | `2.0` | Reserved; path currently uses settle sleeps |

### `settings`

Process-wide `Settings()` instance, imported by vehicle, mission, and FastAPI.

---

## `src/weed_spray/backend/models.py`

Pydantic models for HTTP bodies, telemetry, and the `sitl_template.md` run log.

### `utc_now() -> str`

UTC ISO-8601 timestamp for log rows (`datetime.now(timezone.utc).isoformat()`).

### `class MissionPhase(StrEnum)`

Internal FSM. Not identical to exported `sitl_template` names.

`idle` → `connecting` → `connected` → `fence_set` → `taking_off` → `scanning` → `awaiting_confirm` → `visiting` → `hovering` → `spraying` → `rtl` / `land` / `killed` / `error`.

### `EXPORT_PHASE`

Maps a subset of `MissionPhase` to template names: `scanning→scan`, `hovering`/`spraying→spray_hover`, `rtl→rtl`, `land`/`killed→land`. Unmapped phases are not appended to `phase_log`.

### `class FenceBox`

Local NED metres from home: `north_m` (default 20), `south_m` (−5), `east_m` (15), `west_m` (−15).

### `class Detection`

One plant. JSON field is `"class"` (alias of `class_name`). Fields: `id`, `class_name`, `north_m`, `east_m`, `conf` (1.0), `confirmed`, `visited`, `sprayed`, `t`.

### HTTP bodies

| Model | Used by | Notes |
|---|---|---|
| `InjectRequest` | `POST /detections/inject` | `{detections: Detection[]}` |
| `ConfirmDecision` | nested in confirm | `detection_id`, `decision` = `confirm`\|`reject` |
| `ConfirmRequest` | `POST /confirm` | `ids[]` are confirms; `decisions[]` may reject |
| `ArmRequest` | `POST /scan` | `source` = `rc`\|`dashboard` (default dashboard) |

### Run-log rows

| Model | Role |
|---|---|
| `ConfirmEvent` | Confirm/reject row (`sitl_template` `confirms[]`) |
| `HoverSample` | Spray-hover AGL sample; `missing=true` when lidar is absent or `distance_reading_m` returns `None` (incl. readings **≥ 1 m**) |
| `PumpPulse` | One 0.75 s commanded pulse tied to a detection id |
| `PumpOffEvent` | Failsafe/operator pump-off; `pump_commanded_off` must stay true |
| `PhaseEvent` | Exported phase timeline (`scan`, `spray_hover`, `rtl`, …) |

`PumpOffEvent.type` is one of: `kill`, `rc_loss`, `offboard_loss`, `geofence`, `disconnect`, `rtl`, `failsafe`, `people`, `mission_error`, `shutdown`.

### `class Telemetry`

Last MAVSDK snapshot: `connected`, `armed`, `in_air`, `lat`, `lon`, `north_m`, `east_m`, `ned_down_m` (local NED down, **not** AGL), `relative_alt_m`, `heading_deg`, `distance_sensor_m` (trusted spray hover, dropped at ≥ 1 m), `distance_scan_m` (1-5 m sample only when relative alt is in that same band), `distance_sensor_missing` (true when no usable short-range reading — typical on SIH, including dropped **≥ 1 m** bogus streams), `distance_sensor_stream_alive` (positive finite raw DISTANCE_SENSOR seen in the scan band), `pump_value`, `flight_mode`, `rc_available`.

### `class AppState`

Full GCS state from `GET /state` and `/ws`: phase, telemetry, fence, detections, confirms, last_error, pump_pulses, pump_off_events, hover_agl_m, phase_log, rtsp_url, webrtc_url, mavsdk_address, arm_source, t_start, kind (`sitl`\|`hw`).

---

## `src/weed_spray/backend/geo.py`

Local NED (metres from home) ↔ WGS84 for geofence upload. Flat-earth: 111 320 m per degree latitude; longitude scaled by `cos(lat)`.

### `ned_to_latlon(home_lat, home_lon, north_m, east_m) -> (lat, lon)`

Offset home by north/east metres.

### `fence_corners_latlon(home_lat, home_lon, box) -> list[(lat, lon)]`

Four WGS84 corners of `FenceBox`, clockwise from north-east: NE, SE, SW, NW.

### `lawnmower_waypoints(box, spacing_m) -> list[(north_m, east_m)]`

Scan vertices inside `box`. Rows run north–south, alternating direction. `spacing_m <= 0` becomes 4 m. Endpoints inset 1 m from north/south edges so the path stays inside.

---

## `src/weed_spray/backend/vehicle.py`

MAVSDK wrapper. PX4 listens for offboard APIs on UDP 14540 (we bind). Does **not** write `COM_RCL_EXCEPT` bit 2 or disable `NAV_RCL_ACT`.

### `distance_reading_m(current, relative_alt_m=None, *, mirror_eps_m=0.5, mirror_min_m=1.0, max_trust_m=1.0) -> float | None`

Parse lidar metres for spray hover. `None`, non-numeric, NaN, or `<= 0` → `None` (treated as missing). Readings **≥ `max_trust_m`** (default **1 m**) → `None` so SIH bogus streams (often ~GPS/relative alt, e.g. ~12 m, or high while commanded low) cannot pretend to be AGL. Optional relative-alt mirror drop: when `relative_alt_m` is within `mirror_eps_m` of a reading at least `mirror_min_m`, return `None`; low hover (~0.24–0.32 m) stays kept even if it matches relative alt.

### `class Vehicle`

One PX4 vehicle. Holds a MAVSDK `System`, home lat/lon, pump value, telemetry cache, background tracker tasks, and optional `on_failsafe` callback.

#### `Vehicle.__init__()`

Constructs `System()`, empty telemetry, no tasks. `on_failsafe` is set later by `Mission`.

#### `Vehicle.telemetry` (property) → `Telemetry`

Copy of last snapshot plus live `connected` and `pump_value`.

#### `async Vehicle.connect(address=settings.mavsdk_address)`

Wait for MAVSDK heartbeat, store home from global position, start seven tracker tasks. Does not write PX4 params.

#### `async Vehicle._wait_global_position()`

Block until EKF reports global + home position, then store home lat/lon/relative alt.

#### `async Vehicle._fire_failsafe(kind)`

If `on_failsafe` is set, await it. `kind` is a `PumpOffEvent.type`.

#### Trackers (background tasks)

| Method | Stream | Effect |
|---|---|---|
| `_track_rc` | `rc_status` | After RC was seen once, disappearance fires `rc_loss` |
| `_track_flight_mode` | `flight_mode` | After Offboard was seen, leaving it (except RTL/land/hold) fires `offboard_loss` |
| `_track_position` | `position` | lat/lon/relative_alt_m |
| `_track_local_ned` | `position_velocity_ned` | `north_m`, `east_m`, `ned_down_m` (not AGL) |
| `_track_armed` | `armed` | `telemetry.armed` |
| `_track_in_air` | `in_air` | used for RC-first takeoff |
| `_track_heading` | `heading` | `heading_deg` |
| `_track_distance` | `distance_sensor` | `apply_distance_sample` (1-5 m with relative alt in band → stream alive and `distance_scan_m`; short-range trust → `distance_sensor_m`) |

#### `async Vehicle.upload_fence(box)`

Upload a PX4 **inclusion** polygon from the typed NED box. Raises `RuntimeError` if home is unknown.

#### `async Vehicle.wait_in_air(timeout_s=60)`

RC-first: poll until `in_air`, else `TimeoutError`.

#### `async Vehicle.arm_and_takeoff(agl_m, timeout_s=None)`

Dashboard-first: set takeoff altitude, arm, takeoff, wait until relative alt ≥ 70% of `agl_m`. Timeout is `WEED_TAKEOFF_TIMEOUT_S` (default 20 s; Gazebo `make backend-gz` uses 90). Else `TimeoutError`. Relative alt here is climb-detect only, not spray AGL (issue #27).

#### `async Vehicle.start_offboard_hold(north, east, down)`

Send one NED setpoint then `offboard.start()`. MAVSDK keeps ≥ 2 Hz. One retry on `OffboardError`.

#### `ned_down_for_lidar_band(current_down, lidar_m, min_m, max_m) -> float`

Pure helper (#33): shift NED `down` toward the midpoint of `[min_m, max_m]` using **lidar** metres (not local `z`). Too-high lidar → more positive down (descend); too-low → climb. One-shot only — do not re-apply onto an already-nudged `down` when lidar changes (PR #34).

#### `should_nudge_for_lidar_band(lidar_m, min_m, max_m, last_nudged_lidar_m, *, change_eps_m=0.02) -> bool`

True only for the **first** out-of-band poll (`last_nudged_lidar_m is None`). Later readings wait. Prevents restacking full `(lidar - midpoint)` onto already-nudged NED during partial descent.

#### `async Vehicle.goto_ned(north, east, down, settle_s=2.0)`

Offboard position. `down` is NED z (positive down). Sleeps `settle_s` (FakeVehicle does not sleep).

#### `async Vehicle.wait_lidar_hover_band(min_m, max_m, timeout_s=15.0, north=None, east=None, down=None) -> float`

Poll trusted `DISTANCE_SENSOR` until it is in `[min_m, max_m]`. Proof is lidar, not local `z`. If `north`/`east`/`down` are all set, re-sends that Offboard NED each poll so PX4 does not drop Offboard. At most **one** lidar-error NED nudge, then hold until in-band or timeout. Raises `TimeoutError` with last lidar and relative_alt. FakeVehicle checks immediately (no sleep).

#### `async Vehicle.goto_global_agl(lat_deg, lon_deg, agl_m, settle_s=2.0)`

Offboard global AGL via MAVSDK `PositionGlobalYaw.AltitudeType.AGL` (PX4 `MAV_FRAME_GLOBAL_TERRAIN_ALT_INT`). Sleeps `settle_s` (FakeVehicle records `(lat, lon, agl_m)` and does not sleep). Mission: restart Offboard hold, stream_alive, NED step -1 m then hover, `wait_lidar_hover_band`, then `goto_global_agl`. Requires `WEED_LIDAR_EXPECTED`.


#### `async Vehicle.set_pump(value)`

`action.set_actuator(pump_index, value)` on `[-1, 1]`. OFF is `0.0`. Records `pump_value`. Re-raises `ActionError`.

#### `async Vehicle.pulse_pump(duration_s)`

ON for `duration_s` then OFF in `finally` (never leave the pump latched).

#### `async Vehicle.pump_off(reason) -> PumpOffEvent`

Command actuator 0 and return a log row. `reason` is `PumpOffEvent.type`.

#### `async Vehicle.rtl()`

Stop Offboard if running, then PX4 return-to-launch.

#### `async Vehicle.kill() -> PumpOffEvent`

Pump off, leave Offboard, Hold (or RTL if Hold fails).

---

## `src/weed_spray/backend/mission.py`

Mission state machine: fence → scan → confirm → visit/pulse → RTL. Unconfirmed detections are never sprayed. Hover AGL uses parsed `DISTANCE_SENSOR` (short-range only; **≥ 1 m** → `missing`) or `missing`.

### `class Mission`

Owns `AppState` and sequences `Vehicle` calls for one flight. Constructor sets `vehicle.on_failsafe = self._on_failsafe`.

#### `Mission.snapshot() -> AppState`

Deep copy of mission state plus live telemetry.

#### `Mission._set_phase(phase)`

Set internal phase. If `EXPORT_PHASE` maps it, append a `PhaseEvent`.

#### `async Mission._on_failsafe(kind)`

Pump off unless already `idle`/`killed`. Appends `PumpOffEvent`.

#### `async Mission.connect()`

Connect MAVSDK, stamp `t_start`, phase `connected`.

#### `async Mission.set_fence(box)`

Upload the yard rectangle to PX4 and store it on state.

#### `Mission.inject(req)`

Merge detections by id. Raises `ValueError` if `class` is outside `{dandelion, clover, thistle, mallow}`. Does not confirm.

#### `Mission.confirm(req)`

Record confirm/reject. `ids` are treated as confirm. Raises `ValueError` on unknown ids. Does not pulse.

#### `async Mission.kill()`

Operator kill: pump off, cancel scan/visit task, phase `killed`.

#### `async Mission.hold_for_people()`

People/pets abort: pump off (`type=people`) and PX4 Hold. Phase `killed`.

#### `async Mission.rtl()`

Pump off then return-to-launch.

#### `async Mission.start_scan(arm=None)`

Start background lawnmower. Raises `RuntimeError` if a task is already running. Default arm source is `dashboard`.

#### `async Mission._run()`

Wrap `_run_inner`. On error: phase `error`, pump off `mission_error`. Re-raises `CancelledError`.

#### `async Mission._run_inner()`

Require fence + connected. RC-first waits in-air; else arm/takeoff to scan AGL. Start Offboard hold, walk lawnmower waypoints, then `awaiting_confirm`.

#### `async Mission.visit_now()`

After confirm: visit confirmed ids only. Raises if scan still running.

#### `async Mission._visit_then_rtl()`

Visit loop then RTL; pump-off on exception.

#### `async Mission._visit_confirmed()`

For each confirmed id: XY at 2 m, mark visited, descend to hover, sample AGL (or `missing`), pulse 0.75 s, mark sprayed, climb, next. Unconfirmed ids are never in the target list.

#### `Mission.run_log() -> dict`

JSON object specified by `bot_files/sitl_template.md` / `sitl/summaries/_template.md`. Hover samples with `missing` serialize `agl_m` as the string `"missing"`.

---

## `src/weed_spray/backend/main.py`

FastAPI GCS on `:8000`. Route table: [api.md](api.md).

Module-level `vehicle = Vehicle()` and `mission = Mission(vehicle)` are the live process objects. Tests swap them for `FakeVehicle`.

### `async lifespan(_app)`

On shutdown, `vehicle.pump_off("shutdown")` even if a pulse is mid-sleep. Errors ignored.

### Routes

| Handler | Method / path | Behavior |
|---|---|---|
| `health` | `GET /health` | `{ok, phase, connected, rtsp, mavsdk}` |
| `state` | `GET /state` | Full `AppState` JSON (`class` alias) |
| `connect` | `POST /connect` | MAVSDK bind; **503** if PX4 is silent |
| `fence` | `POST /fence` | Inclusion geofence; **400** on error |
| `scan` | `POST /scan` | Lawnmower; **409** if already running |
| `inject` | `POST /detections/inject` | Merge boxes; best-effort forward to vision; **400** unknown class |
| `confirm` | `POST /confirm` | Human/harness confirm; **400** unknown ids |
| `visit` | `POST /visit` | Confirmed ids only; **409** if scan running |
| `rtl` | `POST /rtl` | Pump off + RTL |
| `kill` | `POST /kill` | Pump off, cancel task, Hold |
| `hold_people` | `POST /hold-people` | Pump off + Hold |
| `run_log` | `GET /run-log` | `sitl_template` JSON |
| `preflight` | `GET /preflight` | FAA reminders, not compliance |
| `ws` | `WebSocket /ws` | Push snapshot every 250 ms |

CORS allows `http://127.0.0.1:8080` and `http://localhost:8080`.

### `run()`

CLI entry `weed-spray`: uvicorn on `WEED_HTTP_HOST:PORT`, no reload.

---

## `src/weed_spray/vision/classes.py`

Frozen v1 class map. `bot_files/weeds_class-map.md`. **Do not renumber.**

| Symbol | Value |
|---|---|
| `NAMES` | `{0: "dandelion", 1: "clover", 2: "thistle", 3: "mallow"}` |
| `NC` | `4` |
| `CLASSES` | `frozenset` of those names |
| `NAME_TO_ID` | reverse map |
| `YAML_RELATIVE` | `"weeds/weeds.yaml"` |

Turf, dirt, crabgrass, plantain, and “other_weed” are unlabeled background. Id 3 is mallow (includes ground ivy).

---

## `src/weed_spray/vision/boxes.py`

Pixel observations from a detector stand-in. Does not import Ultralytics. No north/east.

### `class RawBox`

Frozen detector row: `class_id`, `conf`, normalized `cx`/`cy`/`w`/`h`.

### `parse_boxes(boxes, *, conf_min, imgsz) -> list[dict]`

Keep ids in `NAMES` with `conf >= conf_min` and short side `min(w, h) * imgsz` ≥ 20 px. Unknown indexes are dropped. Each dict is `{class, conf, cx, cy, w, h}`. Empty input returns `[]`.

---

## `src/weed_spray/vision/project.py`

Nadir pixel to local north/east. No default lens. No MAVSDK.

Image-right is body-right (+east at heading 0). Image-down is aft (-north at heading 0). That second sign is the function's convention until a Gazebo frame checks the mount. Georeference stays off.

### `project_nadir(...) -> tuple[float, float] | None`

Args: normalized center, frame size, `hfov_deg`, `height_m`, vehicle north/east, heading degrees, optional fence `(north, south, east, west)`. `None` when height or FOV is missing, the center is outside 0-1, or the point is outside the fence. Image center returns the vehicle point.

---

## `src/weed_spray/vision/runtime.py`

Injector gate for `WEED_YOLO_WEIGHTS`. Does not load a model.

### `runner_started() -> bool`

False until a later story starts the RTSP reader.

### `reset_for_tests()`

Clears the one-shot missing-file log and the runner flag.

### `configure_logging()`

Attach one stderr handler at INFO so a missing-weights line is visible under uvicorn.

### `note_configured_weights()`

Empty env: no log. Path is not a file: log once and stay injector. Path is a file: no reader.

---

## `src/weed_spray/vision/main.py`

Detection injector / YOLO stub on `:8090`. Injected boxes are the v1 pass. In-memory `_boxes` list.

### `class Detection`

One injected plant. `class` must be in `CLASSES` (dandelion, clover, thistle, mallow).

#### `Detection.known_class(value) -> str`

Pydantic validator. Rejects crabgrass / other_weed / anything not in `CLASSES`.

### `class InjectRequest`

`POST /inject` body: `{detections: Detection[]}`.

### Routes

| Handler | Path | Behavior |
|---|---|---|
| `health` | `GET /health` | `mode=injector`, frozen `names`, `weights=None`, `count`. Calls `note_configured_weights`: a missing `WEED_YOLO_WEIGHTS` file logs once and does not start a runner. |
| `detections` | `GET /detections` | Current box list |
| `inject` | `POST /inject` | Upsert by id; does not confirm spray |
| `clear` | `DELETE /detections` | Drop all boxes |

### `run()`

CLI entry `weed-spray-vision`: uvicorn `127.0.0.1:8090`.

---

## `src/weed_spray/vision/train.py`

Train YOLO on `weeds/weeds.yaml`. Does **not** download public archives.

### `IMAGE_EXTS`

`{".jpg", ".jpeg", ".png", ".webp"}`.

### `repo_root() -> Path`

Directory that contains `weeds/weeds.yaml` (cwd, else parents of this file). Fallback: cwd.

### `ROOT` / `YAML`

Resolved once at import.

### `_count_images(split) -> int`

Count RGB files in `weeds/dataset/images/{train,val}`. Ignores `.gitkeep` and non-image files.

### `list_sources()`

Print `bot_files/weeds_sources.md`. Does not download. Reminds the operator to collect backyard photos in `weeds/inbox/`.

### `train(device, epochs, imgsz, model) -> int`

Run Ultralytics on `weeds.yaml`. Returns **2** if train/val is empty or `ultralytics` is missing (`uv sync --extra yolo`). Writes to `var/yolo/weeds`. Returns **0** on success.

### `main(argv=None) -> int`

CLI `weed-spray-train`. `--list-sources` never fetches data. Returns 2 if yaml missing or a frozen class name is absent from yaml.

---

## `src/weed_spray/harness/accept.py`

Live `loop.md` pass/fail script. First fail stops the grade; remaining rows = `blocked`. Pump-off-on-kill still runs if the vehicle was armed.

Constants: `BACKEND=http://127.0.0.1:8000`, `VISION=http://127.0.0.1:8090`, RTSP `127.0.0.1:8554`, `STEPS` = the 10 loop.md labels.

### `rtsp_open() -> bool`

True if MediaMTX answers RTSP `OPTIONS` on `8554/cam` (`RTSP/`, `200`, or `401`). `OSError` → false.

### `write_last_run(path, results)`

Write the 10-step markdown table. Missing steps become `blocked` / `not reached`. Creates parent dirs.

### `main(argv=None) -> int`

Drive the live HTTP sequence. `--out` default `var/last-run.md`. Return 1 if any step failed, 0 if all passed.

Inner `grade(step, ok, notes)`: after the first fail, further grades are `blocked`. Step 10 is special: still executed if `armed`, even after earlier fails.

Step 7 fails when `hover_agl_m` is `missing` (expected on SIH). Step 8 requires exactly one pulse of ≈ 0.75 s.

---

## `dashboard/src/main.tsx`

### Entry

`createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>)`.

---

## `dashboard/src/App.tsx`

### Types

- `Detection` — table row: `id`, `class`/`class_name`, NED metres, `confirmed`/`visited`/`sprayed`.
- `State` — UI snapshot: `phase`, `last_error`, URLs, telemetry subset, detections.
- `empty` — idle `State` before the first backend snapshot.

### `async api(path, init?)`

`fetch('/api' + path)` with JSON headers. Throws `Error` with path, status, and body text on non-OK.

### `CamMonitor({ src, rtsp })`

`<video>` + `hls.js` on `/hls/cam/index.m3u8`. Vite proxies `/hls` to MediaMTX `:8888`.

### `function App()`

Localhost GCS: fence form, arm-source select, confirm/reject, visit, RTL, people hold, kill. Subscribes to `/ws`; falls back to polling `/api/state`.

#### `toggle(id)`

Add or remove a detection id from the confirm/reject selection.

#### `async run(fn)`

Run an API call and surface HTTP errors in the banner.

---

## `dashboard/vite.config.ts`

Vite on port **8080**, `strictPort: true`.

- `/api` → `http://127.0.0.1:8000` with `/api` prefix stripped.
- `/ws` → `ws://127.0.0.1:8000` (`ws: true`).

---

## `tests/fakes.py`

In-process stand-in for MAVSDK `Vehicle`. No PX4, no sleep.

### `class FakeVehicle`

Same async surface as `Vehicle`. Records `gotos`, pulse/takeoff/RTL/kill counts. Home is `40, -105`. `distance_sensor_missing=True`. `drone.action.hold` is `_async_noop`.

Each method mirrors `Vehicle` without UDP: `connect` marks connected; `upload_fence` stores the box; `wait_in_air` / `arm_and_takeoff` set `in_air` immediately; `goto_ned` appends NED and applies `agl_after_descend_m` when `|down|` ≤ 1 m; `wait_lidar_hover_band` checks the band immediately; `goto_global_agl` appends `(lat, lon, agl_m)`; neither sleeps; `pulse_pump` increments `pulses` and leaves pump at 0; `kill` counts and pump-offs.

### `async _async_noop(*_a, **_k)`

PX4 Hold no-op used by `hold_for_people` tests.

---

## `tests/conftest.py`

### `fixture _reset_vision_boxes` (autouse)

Clears `weed_spray.vision.main._boxes` before and after every test so injector state does not leak.

---

## Tests (what each file covers)

| File | Covers |
|---|---|
| `tests/unit/test_geo.py` | NED→lat/lon, clockwise fence corners, lawnmower spacing |
| `tests/unit/test_classes.py` | Class map matches `weeds.yaml`; no crabgrass |
| `tests/unit/test_distance.py` | `distance_reading_m` NaN / ≤0 / junk / **≥ 1 m** / SIH mirrors → `None`; low hover kept |
| `tests/unit/test_models.py` | `"class"` alias, confirm ids+decisions, pump-off type |
| `tests/unit/test_mission.py` | Inject/confirm/reject, unconfirmed never sprayed, RC vs dashboard, kill/people, failsafe idle skip |
| `tests/unit/test_train.py` | Empty dataset count; `--list-sources` does not download |
| `tests/unit/test_harness.py` | Last-run table order; `rtsp_open` false on closed port |
| `tests/unit/test_contracts.py` | Compose ports, dashboard safety strings, `bot_files/` present |
| `tests/unit/test_extract_clip_inbox.py` | Inbox dest guards; skip-if-present; no dataset writes |
| `tests/unit/test_promote_inbox.py` | Split by image; copy jpg+txt; skip unlabeled |
| `tests/integration/test_backend_api.py` | ASGI FastAPI + `FakeVehicle`: connect/fence/inject/confirm/visit/kill |
| `tests/integration/test_vision_api.py` | Inject/get/delete; 422 on unknown class |

No live PX4 in pytest. Live grading is `weed-spray-accept` ([testing.md](testing.md)).

---

## `scripts/extract_clip_inbox.py`

Unlabeled 1 fps JPEG dump from a lawn clip into `weeds/inbox/<stem>/`. Does not box, split train/val, or train.

### `default_clip(media=None) -> Path | None`

First existing of `backyard_weeds.MOV`, `.mov`, `.mp4` under `media/`. Omitting `media` uses module `MEDIA` at **call time** (so tests can monkeypatch).

### `inbox_dest(clip, inbox=None) -> Path`

`inbox / clip.stem.lower()`. Omitting `inbox` uses module `INBOX` at call time.

### `dest_error(dest, inbox=None, dataset=None) -> str | None`

Error if `dest` is not an inbox subfolder or sits under `weeds/dataset/`. Omitting path args uses module `INBOX` / `DATASET` at call time.

### `existing_frames(dest) -> list[Path]`

`frame_*.jpg` / `.jpeg` in `dest`.

### `ffmpeg_argv(clip, dest, fps, quality) -> list[str]`

Host `ffmpeg`: video only, `fps=`, `-q:v`, `frame_%04d.jpg`.

### `extract(...) -> int`

Skip ffmpeg when frames exist unless `--force`. Refresh `SOURCE.md`. Return 2 on dest/clip/ffmpeg failure.

### `main(argv=None) -> int`

CLI. `--dry-run` prints argv. `--force` replaces stills.

---

## `scripts/promote_inbox.py`

Copy boxed inbox jpg+txt into `weeds/dataset/`. Split by image. Does not train.

### `BACKYARD_VAL_FRAMES`

Held-out frame numbers from the backyard clip (thistle, dandelion, mallow, turf negatives).

### `assign_split(stem, source) -> str`

`val` if backyard frame is in the hold-out set; else `train`. Other inbox folders → `val`.

### `promote(...) -> int`

Copy pairs. Skip existing unless `--force`. Return 2 if no boxed stills.

### `main(argv=None) -> int`

CLI. `--source` default `backyard_weeds`.
