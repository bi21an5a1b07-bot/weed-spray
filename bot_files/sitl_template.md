# SITL run log contract

Copy to `sitl/summaries/YYYY-MM-DD-HHMM-<sitl|hw>.md`. Fill from a real dashboard JSON / ulog only. Absent field = `missing`. Do not invent numbers. Do not use `vehicle_local_position.z` as AGL.

Steps match `/workspace/weed-spray/sitl/loop.md`. After grading, copy the pass/fail line into `sitl/last-run.md`.

SIH has no lidar ([simulator comparison](https://docs.px4.io/main/en/simulation/#simulator-comparison)). If `DISTANCE_SENSOR` is absent, `hover_agl_m[]` is `missing` and loop step 7 **fails**.

Pump: MAVSDK `set_actuator(1, value)` / [`MAV_CMD_DO_SET_ACTUATOR`](https://mavlink.io/en/messages/common.html#MAV_CMD_DO_SET_ACTUATOR) param1. Pulse 0.75 s is app sleep (`px4/actuators.md`). Extra pulse vs confirms = defect.

---

## Identity

- kind: `sitl` | `hw`
- t_start / t_end (ISO-8601):
- git / px4_version:
- arm_source: `rc` | `dashboard` | `missing`
- compose: `px4io/px4-sitl` `sihsim_quadx` + RTSP `8554/cam` + backend `8000` + dashboard `8080` + injector `8090` + UDP `14540`

## Geofence corners

`geofence`: `{n,e,s,w}` local meters **or** four GPS corners. Required for loop step 2.

## phase[]

`t`, `name`: `idle` | `scan` | `spray_hover` | `rtl` | `land`

Scan is **2.0 m AGL**, not 6–12 in (`px4/offboard.md`).

## detections[]

`id`, `t`, `class` (`dandelion` | `clover` | `thistle` | `mallow`), `conf`, `x_m`/`y_m` or `lat`/`lon`. Injector is a v1 pass.

## confirms[]

`t`, `detection_id`, `decision` (`confirm` | `reject`). No pulse without a matching confirm. Human (or harness acting as human) only.

## hover_agl_m[]

Spray-hover samples only (`phase == spray_hover`). `t`, `agl_m`, `detection_id`. Source: `DISTANCE_SENSOR` / `distance_sensor.current_distance` (m), downward. **If no distance sensor: `missing` (SIH).** Target 0.15–0.30 m (6–12 in).

## pump_pulses[]

`t`, `duration_s` (default 0.75), `detection_id`, `commanded`. Count must equal confirmed visits.

## pump_off_events[]

`t`, `type` (`kill` | `rc_loss` | `offboard_loss` | `geofence` | `disconnect` | `rtl` | `failsafe`), `pump_commanded_off` (bool). Loop step 10 **required**.

## Loop grade (copy to last-run.md)

| Step | loop.md | pass / fail / blocked |
|---|---|---|
| 1 connect | 14540 + dashboard 8080 + RTSP 8554/cam + injector 8090 | |
| 2 geofence | `geofence` corners present | |
| 3 scan | `phase` scan at 2.0 m, inside fence | |
| 4 detect | `detections[]` ≥ 1 | |
| 5 confirm | subset in `confirms[]` | |
| 6 visit | confirmed ids only, XY then descend | |
| 7 hover | `hover_agl_m[]` or `missing` (fail if missing) | |
| 8 pulse | `pump_pulses[]` duration ≈ 0.75, count = confirms | |
| 9 RTL | `phase` rtl/land, pump off | |
| 10 pump-off on kill | `pump_off_events[]` with `pump_commanded_off=true` | |

First fail. Extra pulses: defect.
