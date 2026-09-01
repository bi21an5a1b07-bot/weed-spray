# SITL

Contract: `bot_files/sitl_loop.md`. Compose: `compose.yaml`.

## Images

Only these three (do not `docker pull` extras at runtime):

- `px4io/px4-sitl:latest` with `PX4_SIM_MODEL=sihsim_quadx`
- `bluenviron/mediamtx:latest`
- `mwader/static-ffmpeg:7.1` (binary is `/ffmpeg`, not on `PATH`)

`network_mode: host` so PX4’s UDP 14540 is the WSL host. One vehicle.

## RTSP

`rtsp://127.0.0.1:8554/cam` is a **file** loop (`media/smoke.mp4` is `testsrc` for connect-smoke). Replace with a lawn clip for a green vision pass. Injected boxes still pass detect-step 4.

Not Gazebo RTP 5600. Not `/dev/video`.

## Accept script

```bash
uv run weed-spray-accept --out var/last-run.md
```

Ten steps from `loop.md`. First fail blocks later rows except **pump-off on kill**, which still runs if the vehicle armed. Step 7 (6–12 in hover) **fails on SIH** when `DISTANCE_SENSOR` is missing.

Realtime only (`PX4_SIM_SPEED_FACTOR` unset).

## Params the code does **not** set

`bot_files/px4_offboard.md`: do not invent `COM_RC_IN_MODE=4`, `COM_RCL_EXCEPT` bit 2, or `NAV_RCL_ACT` disabled. SITL arm-without-radio is an operator/QGC problem, not a silent firmware change.
