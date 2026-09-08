# Acceptance testing (live SITL)

How to run the weed-spray app through the live 10-step accept grade. Normative contract: [`bot_files/sitl_loop.md`](../bot_files/sitl_loop.md). Grader: `weed_spray.harness.accept` (`uv run weed-spray-accept` / `make accept`).

This is **not** `make check` (ruff + pytest with `FakeVehicle`). That gate never starts PX4 — see [testing.md](testing.md).

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
uv run weed-spray         # :8000
(cd dashboard && npm run dev)  # :8080
```

Optional: open http://127.0.0.1:8080 to watch. The harness does not need a human click for confirm — it POSTs `/confirm` as the harness-as-human (backend still requires that message; inject never confirms).

`media/smoke.mp4` is `testsrc` for connect-smoke. Injected boxes still pass detect-step 4. A lawn `.mp4` is for a green vision pass later, not required for this harness path.

## Run the grader

With all four processes up:

```bash
make accept
# same as: uv run weed-spray-accept --out var/last-run.md
```

The script prints the markdown table and writes `--out` (default `var/last-run.md`).

**Default SIH stack:** expect exit code `1`. Step 7 fails (`DISTANCE_SENSOR` missing → hover `missing`); steps 8–9 are then `blocked`. That is a correct SIH run, not a setup failure. Exit `0` only when every step passes (needs rangefinder data — not default compose).

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
| 7 6–12 in hover | Read `hover_agl_m[]` | Samples in 0.15–0.30 m and **not** `missing` |
| 8 0.75 s pump pulse | Read `pump_pulses[]` | Exactly one pulse; duration ≈ 0.75 s |
| 9 RTL | Phase after visit | `rtl` or `killed` |
| 10 pump-off on kill | `POST /kill` | `pump_commanded_off` (still runs if vehicle armed after an earlier fail) |

Order nuance: the harness **injects before scan** (steps numbered 4 then 3 in wall-clock), then grades scan when phase reaches `awaiting_confirm`. Pass/fail rows still use the step names above.

First fail stops further grading (`blocked`). Step 10 still runs if the vehicle was armed.

## Expected SIH result

PX4 SIH has **no** `DISTANCE_SENSOR`. On the default `make sitl` path:

| | Expected |
|---|---|
| Exit code | `1` (not `0`) |
| Step 7 | `fail` — hover samples `missing` |
| Steps 8–9 | `blocked` (first fail stops the grade) |
| Step 10 | still runs if the vehicle armed |

Do not treat GPS / `vehicle_local_position.z` as AGL. Do not invent rangefinder PX4 params to fake a green table. "Good enough for SIH" = processes up + steps 1–6 and 10 behaving as above + honest step 7 fail — **not** `make accept` exit `0`.

A full green table (exit `0`) needs rangefinder data (hardware or a Gazebo lidar profile). That is **not** the default compose.

## After the run

1. Read `var/last-run.md` (step / result / notes).
2. Tear down Docker when done: `make down` (or `make sitl-down`).
3. Host processes: Ctrl-C the vision, backend, and dashboard terminals.

## Do not

- Auto-confirm a spray (harness may POST `/confirm`; code must still require it).
- Arm / Offboard / pulse a pump on **real** hardware from this path.
- Invent PX4 params (`COM_RCL_EXCEPT` bit 2, `NAV_RCL_ACT=0`, etc.) — [sitl.md](sitl.md), `bot_files/px4_offboard.md`.
- Start accept from a Grok Bot VM / cloud agent (no Docker there for this loop).
- Call `make accept` without SITL + the three host apps (step 1 will fail).

## Related

- Contract: [`bot_files/sitl_loop.md`](../bot_files/sitl_loop.md)
- Short pointers: [testing.md](testing.md), [sitl.md](sitl.md), [cli.md](cli.md)
- Install / manual dashboard path: [getting-started.md](getting-started.md)
