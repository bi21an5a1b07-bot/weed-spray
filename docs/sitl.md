# SITL

Contract: `bot_files/sitl_loop.md`. Default compose: `compose.yaml` (SIH). Opt-in Gazebo: `compose.gazebo.yaml`.

## Images (default SIH)

Only these three on `compose.yaml` (do not `docker pull` extras at runtime):

- `px4io/px4-sitl:latest` with `PX4_SIM_MODEL=sihsim_quadx`
- `bluenviron/mediamtx:latest`
- `mwader/static-ffmpeg:7.1` (binary is `/ffmpeg`, not on `PATH`)

`network_mode: host` so PX4’s UDP 14540 is the WSL host. One vehicle.

The `px4io/px4-sitl` entrypoint rewrites mavlink `-t` to `host.docker.internal` whenever that name resolves (meant for Docker Desktop). On this WSL box that address is the Windows host, not loopback, so MAVSDK never sees HEARTBEAT. Compose pins `extra_hosts: host.docker.internal:127.0.0.1` so `-t` stays localhost.

## RTSP

`rtsp://127.0.0.1:8554/cam` is a **file** loop (`media/smoke.mp4` is `testsrc` for connect-smoke). Replace with a lawn clip for a green vision pass. Injected boxes still pass detect-step 4.

The dashboard does not play RTSP. It plays **HLS** at `/hls/cam/index.m3u8` (Vite → MediaMTX `:8888`). WebRTC `:8889` remains available but ICE from Windows→WSL often closes the peer connection.

Default SIH path is not Gazebo RTP 5600 and not `/dev/video`. (On `make sitl-gz`, RTP `:5600` is cam ingest only — see below.)

## Opt-in Gazebo (`make sitl-gz`)

Accurate profile for issue [#19](https://github.com/bi21an5a1b07-bot/weed-spray/issues/19). **Does not** replace default `make sitl` (SIH file RTSP remains the light path).

- Compose: `compose.gazebo.yaml` with project `name: weed-spray-gz` (SIH uses `name: weed-spray-sih` in `compose.yaml`)
- Targets: `make sitl-gz` / `make sitl-gz-down` use `docker compose -p weed-spray-gz …`; SIH counterparts use `-p weed-spray-sih`. `make down` tears both. Host-network (UDP **14540** + MediaMTX): `make sitl` runs **smoke-video**, then `sitl-gz-down`, then SIH up; `make sitl-gz` runs `sitl-down` then Gazebo up — do not run both composes at once. Project isolation means one profile’s `down` cannot remove the other.
- Images (exactly those in `compose.gazebo.yaml`; do not `docker pull` extras at runtime):
  - `px4io/px4-sitl-gazebo:latest` with `PX4_SIM_MODEL=gz_x500_lidar_down`, `HEADLESS=1`
  - `bluenviron/mediamtx:latest` (config `sitl/mediamtx-gazebo.yml`)
- Model overlay: repo `sitl/gz/models/x500_lidar_down` merges downward `mono_cam` onto stock `gz_x500_lidar_down` (sourced from PX4-gazebo-models `x500_mono_cam_down`)
- **Vehicle camera is wired:** Gazebo GstCameraSystem UDP RTP **`:5600`** H264 PT 96 (ingest only — not a second GCS path) → MediaMTX `udp+rtp://127.0.0.1:5600` + H264 PT 96 `rtpSDP` in `sitl/mediamtx-gazebo.yml` → **`rtsp://127.0.0.1:8554/cam`** (one GCS URL). Dashboard still HLS `:8888`. **No** `cam-bridge`. **No** bare ffmpeg `rtp://`. **No** `smoke.mp4` on this profile.
- WSL: `network_mode: host` + `extra_hosts: host.docker.internal:127.0.0.1` (same HEARTBEAT fix as SIH)
- Do not start Gazebo on the shared Grok Bot VM — operator WSL only (AWS later only if RAM allows)

**Hover command (app seam, PR #25):** default `WEED_HOVER_ALTITUDE_MODE=ned` still does `goto_ned(..., down=-hover_agl_m)` (SIH). Opt-in `offboard_agl`: **latch** scan-height `distance_sensor_stream_alive` **before** NED hover (hover-height SIH mirrors can clear the telem flag). Stream-alive sets only when both ds and `relative_alt` are contemporaneous scan-height (`[1, 5]` m) and not a mirror; `relative_alt is None` or a later mirror **clears** it (no lag unlock). Then NED approach to hover. After descend: trusted `distance_reading_m` in `[hover_min_m, hover_max_m]` **and** the latched stream_ok. Only then `Vehicle.goto_global_agl` — MAVSDK `AltitudeType.AGL` / `MAV_FRAME_GLOBAL_TERRAIN_ALT_INT`. `hover_agl_m` is **positive AGL metres**. **No PX4 params written.**

**Not claimed live:** PX4 `MPC_ALT_MODE` terrain hold is still **Position/Altitude only, not Offboard** ([PX4 terrain following / holding](https://docs.px4.io/main/en/flying/terrain_following_holding.html)). Do **not** fake AGL with local `z`. Do not invent `EKF2_RNG_*`, `COM_RCL_EXCEPT`, `NAV_RCL_ACT=0`, or `COM_RC_IN_MODE=4`. Whether terrain-alt Offboard actually holds 0.15–0.30 m on `gz_x500_lidar_down` is **operator WSL UAT** — put `WEED_HOVER_ALTITUDE_MODE=offboard_agl` on the **backend** (`uv run weed-spray`), not on `make sitl-gz`. Grade step 7 from `DISTANCE_SENSOR`, not `relative_alt`. Paste `var/last-run.md` if it does not hold.

Live gz `make accept` exit `0` is **not** claimed (cam path landed; Offboard AGL hover UAT still open on #19). SIH bar unchanged (exit `1`, step 7 missing). See [acceptance.md](acceptance.md).

## Accept script

Full operator runbook: [acceptance.md](acceptance.md).

```bash
make accept
# same as: uv run weed-spray-accept --out var/last-run.md
```

Ten steps from `bot_files/sitl_loop.md`. First fail blocks later rows except **pump-off on kill**, which still runs if the vehicle armed. Step 7 (6–12 in hover) **fails on SIH** when `DISTANCE_SENSOR` is missing.

Realtime only (`PX4_SIM_SPEED_FACTOR` unset).

## Params the code does **not** set

`bot_files/px4_offboard.md`: do not invent `COM_RC_IN_MODE=4`, `COM_RCL_EXCEPT` bit 2, or `NAV_RCL_ACT` disabled. SITL arm-without-radio is an operator/QGC problem, not a silent firmware change.
