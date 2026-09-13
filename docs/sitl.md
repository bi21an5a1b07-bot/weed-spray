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

Not Gazebo RTP 5600. Not `/dev/video`.

## Opt-in Gazebo (`make sitl-gz`)

Accurate profile for issue [#19](https://github.com/bi21an5a1b07-bot/weed-spray/issues/19) (first slice). **Does not** replace default `make sitl`.

- Compose: `compose.gazebo.yaml`
- Targets: `make sitl-gz` / `make sitl-gz-down`; `make down` tears SIH **and** Gazebo
- Image / model: `px4io/px4-sitl-gazebo:latest` with `PX4_SIM_MODEL=gz_x500_lidar_down`, `HEADLESS=1`
- Also: MediaMTX. **No** ffmpeg / `smoke.mp4` publisher on this profile
- WSL: `network_mode: host` + `extra_hosts: host.docker.internal:127.0.0.1` (same HEARTBEAT fix as SIH)
- Do not start Gazebo on the shared Grok Bot VM — operator WSL only (AWS later only if RAM allows)
- Images stay exactly those in `compose.gazebo.yaml`; do not `docker pull` extras at runtime

**Vehicle camera → `8554/cam` is not wired** (stock `gz_x500_lidar_down` has no cam). Follow-up on #19.

**Hover / lidar-hold blocker:** PX4 `MPC_ALT_MODE` terrain hold is **Position/Altitude only, not Offboard** ([PX4 terrain following / holding](https://docs.px4.io/main/en/flying/terrain_following_holding.html)). Do **not** fake AGL with local `z`. Do not invent `EKF2_RNG_*`, `COM_RCL_EXCEPT`, `NAV_RCL_ACT=0`, or `COM_RC_IN_MODE=4`.

Live gz `make accept` exit `0` is **not** available yet. SIH bar unchanged (exit `1`, step 7 missing). See [acceptance.md](acceptance.md).

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
