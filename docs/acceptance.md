# Acceptance testing (live SITL)

How to run the weed-spray app through the live 10-step accept grade. Normative contract: [`bot_files/sitl_loop.md`](../bot_files/sitl_loop.md). Grader: `weed_spray.harness.accept` (`uv run weed-spray-accept` / `make accept`).

This is **not** `make check` (ruff + pytest with `FakeVehicle`). That gate never starts PX4 — see [testing.md](testing.md).

Remote AWS EC2 operator host path (SprayPO start/stop, $10/mo cap): [acceptance-aws.md](acceptance-aws.md). WSL remains the primary laptop path.

## SIH vs opt-in Gazebo

| Path | How | Accept bar today |
|---|---|---|
| **SIH (default)** | `make sitl` (`compose.yaml`) | Exit `1`; step 7 missing / fail — honest SIH bar |
| **Gazebo (opt-in)** | `make sitl-gz` + `make backend-gz` | Vehicle cam on `rtsp://127.0.0.1:8554/cam`. Exit `0` is allowed when step 7 is a real lidar sample in 0.24–0.32 m. A recorded green table is not a substitute for this run. |

Default `make sitl` is unchanged. Do not start Gazebo on the shared bot VM. Details: [sitl.md](sitl.md).

## What "green" means

Two different bars:

1. **Processes up** — the four rows below are running (required before `make accept`).
2. **Full accept table** — every step `pass` and exit `0`. Default SIH cannot hit this (step 7); see [Expected SIH result](#expected-sih-result).

All of these are up on the **operator WSL** host (not a Grok Bot VM; do not start Docker from Bot):

| Process | How | Port / bind |
|---|---|---|
| PX4 SIH + MediaMTX + ffmpeg file RTSP | `make sitl` (`compose.yaml` only) | UDP **14540** offboard; RTSP `8554/cam` |
| Vision injector | `uv run weed-spray-vision` or `make vision` | HTTP **8090** |
| Backend GCS | `uv run weed-spray` or `make backend` | HTTP **8000**, MAVSDK `udpin://0.0.0.0:14540` |
| Dashboard | `(cd dashboard && npm run dev)` or `make dashboard` | HTTP **8080** |

Then the harness drives connect → fence → inject → scan → confirm subset → visit → hover → pump → RTL → kill, and writes `var/last-run.md`.

No USB, no serial, no real radio, no real pump. One vehicle. Realtime only (`PX4_SIM_SPEED_FACTOR` unset).

## Prerequisites

- WSL2 Ubuntu with Docker, [mise](https://mise.jdx.dev/walkthrough.html), host `ffmpeg` (for `make smoke-video`)
- Repo install once:

```bash
mise trust && mise install && mise run install
# or: uv sync --extra dev && (cd dashboard && npm install)
```

- Compose images stay exactly those in `compose.yaml` (`px4io/px4-sitl` + `sihsim_quadx`, MediaMTX, `mwader/static-ffmpeg:7.1`). Do not pull extras at runtime. See [sitl.md](sitl.md).

## Start order

Four terminals (or equivalent). Backend / vision / dashboard stay on the **host**; compose is Docker only.

```bash
make sitl                 # builds media/smoke.mp4 if missing, then docker compose up -d
uv run weed-spray-vision  # :8090
uv run weed-spray         # :8000  (SIH). For make sitl-gz: make backend-gz
(cd dashboard && npm run dev)  # :8080
```

`make accept` only checks that port 8080 answers. It does not open the page. Any UAT that claims the dashboard works must also run [Dashboard in Chrome](#dashboard-in-chrome). The harness still POSTs `/confirm` itself. A click in the window is not a confirm.

`media/smoke.mp4` is `testsrc` for connect-smoke. Injected boxes still pass detect-step 4. A lawn `.mp4` is for a green vision pass later, not required for this harness path.

## Run the grader

With all four processes up:

```bash
make accept
# same as: uv run weed-spray-accept --out var/last-run.md
```

The script prints the markdown table and writes `--out` (default `var/last-run.md`).

**Default SIH stack:** `weed-spray-accept` exits `1`. Step 7 fails (hover samples `missing` — no usable short-range lidar). SIH may emit bogus `DISTANCE_SENSOR` readings. Values **≥ 1 m** are dropped. A short value is still logged `missing` while `WEED_LIDAR_EXPECTED` is false, and the ned path still pulses. Steps 8–9 are then `blocked`. That is a correct SIH run, not a setup failure. Exit `0` only when every step passes (needs real rangefinder in the 0.24–0.32 m band — not default compose).

`make accept` is that program under GNU make. Make prints `make: *** [Makefile:43: accept] Error 1` and **make itself exits 2**. The `1` is the grader. The `2` is make's "recipe failed" code. Do not treat exit 2 as a second failure. `uv run weed-spray-accept --out var/last-run.md` exits `1` directly, with no make wrapper.

## The 10 steps (what the harness does)

Source of truth for pass criteria: `bot_files/sitl_loop.md`. Implementation: `src/weed_spray/harness/accept.py`.

| Step | Harness action | Pass notes |
|---|---|---|
| 1 connect | `POST /connect`; checks RTSP OPTIONS on `8554/cam`, dashboard `:8080`, vision `/health` | All four up |
| 2 typed geofence | `POST /fence` box N20 S-5 E15 W-15 | Fence accepted |
| 3 scan | `POST /scan` `{source: "dashboard"}`; wait for `awaiting_confirm` | Phase = awaiting_confirm (≤180 s) |
| 4 inject or detect | `POST /detections/inject` w1 dandelion, w2 clover, w3 thistle | ≥1 detection (fake boxes OK) |
| 5 confirm subset | `POST /confirm` `{ids: ["w1"]}` only | Confirmed = w1; w2/w3 not confirmed |
| 6 visit | `POST /visit`; wait for rtl/killed/error | w1 visited; w2 not visited |
| 7 spray hover | Read `hover_agl_m[]` | Samples in 0.24–0.32 m and **not** `missing` |
| 8 0.75 s pump pulse | Read `pump_pulses[]` | Exactly one pulse; duration ≈ 0.75 s |
| 9 RTL | Phase after visit | `rtl` or `killed` |
| 10 pump-off on kill | `POST /kill` | `pump_commanded_off` (still runs if vehicle armed after an earlier fail) |

Order nuance: the harness **injects before scan** (steps numbered 4 then 3 in wall-clock), then grades scan when phase reaches `awaiting_confirm`. Pass/fail rows still use the step names above.

First fail stops further **grading** (`blocked`). It does not undo work the vehicle already did. On a correct SIH run, step 8 can read `blocked` while `pulses=1` and `durations=[0.75]`, and step 9 can read `blocked` while the phase is already `rtl`. The visit pulsed and started home before the grader stopped scoring. Step 10 still runs if the vehicle was armed.

## Expected SIH result

Default PX4 SIH still expects an honest fail on hover AGL. SIH may publish a bogus `DISTANCE_SENSOR` (often tracking GPS / relative alt, e.g. ~12 m). Readings **≥ 1 m** are dropped (`distance_reading_m`). A short reading is logged `missing` too while `WEED_LIDAR_EXPECTED` is false, so it is not treated as hover AGL. Real spray-hover lidar ~0.24–0.32 m is kept only when a lidar is declared. On the default `make sitl` path:

| | Expected |
|---|---|
| Grader exit | `1` (not `0`). `make accept` then exits `2` because make reports a failed recipe |
| Step 7 | `fail` — hover samples `missing` |
| Steps 8–9 | `blocked` (first fail stops the grade) |
| Step 10 | still runs if the vehicle armed |

Do not treat GPS / `vehicle_local_position.z` as AGL. Do not invent rangefinder PX4 params to fake a green table. "Good enough for SIH" = processes up + steps 1–6 and 10 behaving as above + honest step 7 fail — **not** `make accept` exit `0`.

Exit `0` only with a real rangefinder sample in the 0.24–0.32 m band (Gazebo `make sitl-gz` + `make backend-gz`, or hardware). Default compose remains SIH, and SIH step 7 stays a fail. Do not substitute GPS or local `z`.

`make accept` does **not** exercise YOLO, the dashboard page, georeference, or the train gate. The page is [Dashboard in Chrome](#dashboard-in-chrome). The rest are the next section. Run `make accept` with `WEED_YOLO_GEOREFERENCE` unset so step 4 stays the harness inject.

## Dashboard in Chrome

Required whenever the dashboard is part of the claim. `dash=True` in `var/last-run.md` is only "port 8080 answered". It is not this check.

Drive a **visible** Chrome window through the [Chrome DevTools MCP server](https://github.com/ChromeDevTools/chrome-devtools-mcp/) (`chrome-devtools-mcp`). Do not pass `--headless`. Do not satisfy this section with `curl`, a screenshot flag on `chrome.exe`, or Playwright.

Register it in the user config `~/.grok/config.toml` (not in this repo) and start a new session so the tools are connected:

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest", "--isolated", "--viewport=1280x800", "--no-usage-statistics"]
startup_timeout_sec = 120
```

`--isolated` is a throwaway profile. This session runs in WSL, so the server must start a Chrome that Linux can drive (`DISPLAY` is already set). Do not point `--executablePath` at Windows `chrome.exe` under `/mnt/c`. Do not add this package to `dashboard/package.json`.

With `make sitl`, vision, backend, and `npm run dev` already up, and georeference unset:

1. `new_page` → `http://127.0.0.1:8080`. A window must appear. The server starts Chrome on this call, not merely by being connected.
2. `wait_for` the text `HLS lags RTSP` and `Kill (pump off)`.
3. `take_snapshot` and `take_screenshot` at 1280×800.
4. `list_console_messages` and `list_network_requests`.
5. `resize_page` to 390×844. Snapshot and screenshot again.

Pass when all of these are true at both sizes:

- The page is the weed-spray dashboard, not a connection error.
- The snapshot has a video and the sentence `HLS lags RTSP, so a rectangle is not frame-locked.`
- **Confirm selected** and **Kill (pump off)** are both present. Kill is outside the camera frame and still reachable at 390 px.
- No detection rectangle. This stack is the injector.
- The picture is **not** the drone. `make sitl` loops `media/smoke.mp4` (a test pattern) into `rtsp://127.0.0.1:8554/cam`. A color-bar frame is the correct SIH video. The vehicle camera is only `make sitl-gz`, on this same page address. A late HLS segment is a note, not by itself a failure.
- No uncaught page error. `/api/state` and `/api/preflight` are not failed requests.

Do not click Connect, Scan, Confirm, or Kill. Those talk to the vehicle. `take_snapshot` is the source of element ids. `click` uses that id only in a later pass that has a `y*` box. Then `close_page`.

### Gazebo picture, before any `y*` spray

This is a separate Chrome pass. Do it once on `make sitl-gz` plus `make backend-gz`, with vision and the dashboard up. Leave `WEED_YOLO_GEOREFERENCE` unset so nothing is placed or sprayed. `new_page` the same `http://127.0.0.1:8080`.

The video must be the vehicle's forward, 15°-down camera, not `smoke.mp4`. Pick one object you can see in the Gazebo world (the ground ahead, or a known model) and record which edge of the picture is the nose. Image-right is body-right in the math. Image-up versus the nose is **not** proven until this note exists. If the picture is upside down or backwards relative to that object, fix the projection. Do not add a hidden flip, and do not spray a `y*` row. Do not click Connect, Scan, Confirm, or Kill for this look.

## Vision and georeference

`make accept` is the flight loop with injected boxes. The detector, the overlay, plant placement, and the train gate are separate. None of them may set `confirmed`. A click is not a confirm.

Do not turn `WEED_YOLO_GEOREFERENCE` on for the `make accept` run. Leave it unset.

### What each stack can prove

| Check | SIH file loop | Gazebo camera | Needs weights |
|---|---|---|---|
| Injector health, inject is not confirm | yes | yes | no |
| Missing weights file stays injector | yes | yes | no |
| Weights file, no `yolo` extra: process up, `camera: false`, no boxes | yes | yes | a dummy file |
| Pixel boxes on `GET /detections` and the dashboard | yes, if the clip is the lawn video | frames arrive; a backyard model will not see sim grass | yes, and `uv sync --extra yolo` |
| New mission rows from those pixels | no. The recording is not the vehicle's view | only during scan, with live scan-height lidar and a sourced lens | pixels from the reader |
| Hover step 7 | fail, `missing` | pass only if the sample is in 0.24–0.32 m | no |
| Train refuses an empty class or an orphan label | host only. No PX4 | host only | no |

There is no HTTP call that inserts a pixel box. `POST /inject` is north/east plants. Georeference reads `GET /detections` from the reader. If Gazebo emits no boxes, write "blocked: no pixel rows". Do not inject `w1` and call that a detector test.

### 1. Injector (default)

```bash
uv run weed-spray-vision
curl -s http://127.0.0.1:8090/health
```

Expect `mode` `injector`, `weights` null, `ok` true. Then:

```bash
curl -s -X POST http://127.0.0.1:8090/inject \
  -H 'content-type: application/json' \
  -d '{"detections":[{"id":"w1","class":"dandelion","north_m":1,"east_m":2,"conf":0.9}]}'
```

The body is the box. It has no `confirmed` field. `GET http://127.0.0.1:8000/vision/boxes` (backend up) returns `boxes: []` because that row has no `cx`. The dashboard overlay stays empty. The detections table still shows `w1` after the backend inject. **Confirm selected** is still required before visit.

### 2. Missing weights file

```bash
WEED_YOLO_WEIGHTS=/tmp/no-such-weights.pt uv run weed-spray-vision
```

Process stays up. `GET /health` is still `injector` / `weights` null. The log contains one line: `WEED_YOLO_WEIGHTS /tmp/no-such-weights.pt is missing; staying injector`. A second `GET /health` does not log it again.

### 3. Weights file, YOLO package not installed

```bash
touch /tmp/empty.pt
WEED_YOLO_WEIGHTS=/tmp/empty.pt uv run weed-spray-vision
curl -s http://127.0.0.1:8090/health
curl -s http://127.0.0.1:8090/detections
```

Expect `mode` `yolo`, `camera` false, `ok` true, `detections` `[]`. The log says ultralytics is not installed. The process does not exit.

### 4. Reader on the RTSP URL

Install the extra once: `uv sync --extra yolo`. Point `WEED_YOLO_WEIGHTS` at `var/yolo/weeds/weights/best.pt` (do not commit the file). `WEED_YOLO_DEVICE=cpu` unless the GPU is actually visible; then `0`.

- **See** (file loop): publish a lawn clip on `:8554/cam`, not `media/smoke.mp4`. `make sitl` loops `smoke.mp4` for connect-smoke only. Georeference **off**.
- **Place** (Gazebo): `make sitl-gz` so `:8554/cam` is the vehicle camera. A backyard-trained model will usually emit nothing. That is a blocked place-check, not a failed flight.

While the reader is running:

```bash
curl -s http://127.0.0.1:8090/health
curl -s http://127.0.0.1:8090/detections
curl -s http://127.0.0.1:8000/vision/boxes
```

`camera` true after the stream opens. Each detection has `class`, `conf`, `cx`, `cy`, `w`, `h`, `frame_w`, `frame_h`, `frame_t`. No `north_m` or `east_m`. `GET /vision/boxes` repeats only rows that have `cx`. Class is one of dandelion, clover, thistle, mallow. Anything else is dropped. Confidence under `0.5`, and a short side under 20 px at `imgsz` 640, are dropped.

Stop the camera or the weights fail to load: `GET /detections` goes back to `[]` and `camera` is false. The last frame must not stick.

Dashboard rectangles are judged in Chrome via [Dashboard in Chrome](#dashboard-in-chrome), not by curl. Class and confidence are on the rectangle. The caption says HLS lags RTSP, so the rectangle is not frame-locked. With georeference off the rectangles have no id: clicking one does not select a table row and does not confirm. **Kill** stays outside the video frame at 1280 px and at 390 px.

### 5. Forward camera and arrival

The Gazebo overlay looks forward and 15° down (`WEED_CAM_TILT_DEG=15`). A centered box is a plant about `h / tan(15°)` metres ahead at scan height, not under the aircraft. `h` is `distance_scan_m`.

Georeference still needs `WEED_CAM_HFOV_DEG`. The sourced lens is 99.7° (1.74 rad in the `mono_cam` model cited in [sitl.md](sitl.md)). Leave it unset and the scan stores no `y*` rows (`camera tilt unset` or `camera HFOV unset`). Do not use 90°.

With both set, during scan only:

- The row’s north/east is the ground hit. It is unconfirmed.
- `arrival_time_s` is horizontal distance divided by closing speed (`vn_m_s`, `ve_m_s`). Stopped or flying away yields no time. That time does not start a descent.
- On the visit, hover descent starts only when horizontal position is within `WEED_ARRIVAL_TOLERANCE_M` (0.5 m) of the stored point. If that wait times out, the pump does not pulse and `last_error` contains `not over`.
- Tilt unset, or tilt 90°, does not add this wait. `make accept` leaves tilt unset.

Image-right is body-right in the math. Which way is up is the [Gazebo picture](#gazebo-picture-before-any-y-spray) check. Do not spray a `y*` row until that note exists.

### 6. Georeference (Gazebo scan only)

Do not enable this on SIH. `observe_pixels` does not read `WEED_LIDAR_EXPECTED`. A SIH `DISTANCE_SENSOR` sample that sits in 1–5 m next to relative altitude fills `distance_scan_m` and would place plants from a bogus height. SIH stays at the default `WEED_YOLO_GEOREFERENCE` unset.

On Gazebo, backend env (same process as `make backend-gz`):

- `WEED_YOLO_GEOREFERENCE=1`
- `WEED_CAM_TILT_DEG=15` — must match the SDF mount (`mono_cam` pitch 0.2618 rad forward). Same value as §5. Do **not** set `WEED_CAM_TILT_DEG=90` while the SDF/camera stay 15° forward: that desyncs the gate vs geometry and makes visit/spray aim under the aircraft instead of the weed ~`h/tan(15°)` ahead.
- `WEED_CAM_HFOV_DEG` set from the `mono_cam` model inside the image you actually started. `sitl/gz/models/x500_lidar_down/model.sdf` only includes `model://mono_cam`. It does not state a field of view. The unit tests use 90° as a hand calculation. That number is not the vehicle lens. If you have not read the model, leave the variable unset.

Unset tilt, unset lens, or no live scan-height lidar: scan still finishes, no `y*` rows, and `last_error` says the lidar is missing, `camera tilt unset`, or `camera HFOV unset`. It must not mention substituting relative altitude or local `z`.

During **scan** only, with `telemetry.distance_sensor_stream_alive` true and `distance_scan_m` in 1–5 m (about the 2.0 m lawnmower height, not the 0.27 m hover reading):

- New rows are `y1`, `y2`, … unconfirmed. They do not replace an injected `w1`.
- Two close hits of the same class (within `WEED_YOLO_ASSOC_M`, default 0.35 m) stay one id. A different class, or the same class farther than that, is a second id.
- Place-check uses the **forward** ground hit from `project_oblique`, not nadir under the vehicle. Image center is **not** the vehicle's `north_m` / `east_m`: at tilt 15° and height `h` it is about `h / tan(15°)` metres ahead along heading (~7.46 m at `h` = 2 m). Image-right is body-right (+east when heading is 0). Image-down pitches with the camera (aft only when tilt is 90° / nadir). Which way is up is the [Gazebo picture](#gazebo-picture-before-any-y-spray) check, done with georeference off and without clicking Connect, Scan, Confirm, or Kill. If that picture is upside down or backwards, fix the projection. Do not add a hidden flip, and do not spray a `y*` row until the note exists.
- A point outside the typed fence is dropped.
- Confirm one id. Later frames must not move it, and `confirmed` stays true. A rejected id stays unconfirmed.
- After the phase leaves `scanning`, new pixels add no ids.
- Kill during scan cancels the poll. The lawnmower does not abort just because the vision worker is down (log: `vision poll failed`).
- `GET /vision/boxes` adds `id` on a pixel that matches a `y*` row, and only while lidar, lens, tilt, and pose are present. Clicking that rectangle selects the same table row as the checkbox. **Confirm selected** is still the button that allows a visit. Unconfirmed ids do not pulse.

Hover trust is unchanged: a sample at or above 1 m does not set `distance_sensor_m`. A sample outside the 1–5 m scan band clears `distance_scan_m`. Do not georeference from a stale scan height after the stream goes quiet.

### 7. Train gate (no PX4, no download)

```bash
uv run weed-spray-train --list-sources
```

Prints `bot_files/weeds_sources.md` and does not download.

```bash
uv run weed-spray-train
```

Exit 2 when `weeds/dataset/images/train` or `val` has no images, or when any of the four classes has zero label rows **paired** to an image in `images/train`. The message names the class (`dandelion`, `clover`, `thistle`, or `mallow`). A `labels/train/*.txt` whose stem has no matching image does not count. Clover may be absent from the backyard clip; do not describe that class as detected, and do not lower `WEED_YOLO_CONF` to hide it.

A real training run is operator work on the GPU after the gate passes. It is not part of `make accept`, and the weights stay out of git.

## After the run

1. Read `var/last-run.md` (step / result / notes).
2. Tear down Docker when done: `make down` (SIH **and** Gazebo). Or `make sitl-down` / `make sitl-gz-down` for one profile.
3. Host processes: Ctrl-C the vision, backend, and dashboard terminals.

## Do not

- Auto-confirm a spray (harness may POST `/confirm`; code must still require it).
- Arm / Offboard / pulse a pump on **real** hardware from this path.
- Invent PX4 params (`COM_RCL_EXCEPT` bit 2, `NAV_RCL_ACT=0`, etc.) — [sitl.md](sitl.md), `bot_files/px4_offboard.md`.
- Start accept from a Grok Bot VM / cloud agent (no Docker there for this loop).
- Call `make accept` without SITL + the three host apps (step 1 will fail).
- Call the dashboard checked because port 8080 answered, or because Chrome was headless. The page check is [Dashboard in Chrome](#dashboard-in-chrome).

## Related

- Contract: [`bot_files/sitl_loop.md`](../bot_files/sitl_loop.md)
- Short pointers: [testing.md](testing.md), [sitl.md](sitl.md), [cli.md](cli.md)
- Install / manual dashboard path: [getting-started.md](getting-started.md)
