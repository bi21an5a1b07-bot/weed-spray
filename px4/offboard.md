# weed-spray Offboard / goto

**Date:** 2026-08-30. Sources fetched this date.  
Notes for Grok Build (`/home/behmann/src/grok/drone_control`). **This Bot does not send commands.**

First target: PX4 SITL. No Gazebo camera required. Companion not in the SITL loop.

## Connect

```python
await drone.connect(system_address="udpin://0.0.0.0:14540")
```

PX4 offboard/API UDP **14540**. Older docs `udp://:14540`. QGC **14550**.

https://docs.px4.io/main/en/simulation/  
https://github.com/mavlink/MAVSDK-Python/blob/main/examples/offboard_position_ned.py

## Sequence

Software must not auto-spray. RC in hand whenever motors can spin.

| Step | What | Altitude |
|---|---|---|
| 1 | Typed rectangle geofence, Home inside | — |
| 2 | Arm / takeoff: **RC-first or dashboard-first** (operator choice) | climb to scan height, not 6–12 in |
| 3 | Lawnmower scan. YOLO/injector on the laptop | **2.0 m AGL** (proposed) |
| 4 | Operator confirms a subset | hold scan height |
| 5 | Per confirmed: **goto XY at scan height**, then **descend**, hover **0.15–0.30 m**, pulse pump 0.75 s, pump off, next | spray hover only here |
| 6 | RTL / land. Pump off | RTL altitude, not 6–12 in |

Abort: `set_actuator(1, 0)` then RC / `GF_ACTION`. See `actuators.md`.

https://docs.px4.io/main/en/flight_modes/offboard  
https://docs.px4.io/main/en/flying/geofence

Offboard needs ≥ 2 Hz setpoints **before** the mode switch. MAVSDK Offboard resends at 20 Hz after `start()`. Set a setpoint before `start()`.

Position setpoints only (not velocity-only, not direct motors). Copter frames: `MAV_FRAME_LOCAL_NED` or `MAV_FRAME_GLOBAL_*` including `MAV_FRAME_GLOBAL_TERRAIN_ALT_INT`. NED **z is down**.

**6–12 in:** GPS cannot hold it. `MPC_ALT_MODE=2` terrain hold is documented for **Position/Altitude, not Offboard**. Offboard AGL via EKF2 range height or `PositionGlobalYaw.AltitudeType.AGL` is **unproven**. SIH has **no** `DISTANCE_SENSOR` — do not treat local z as AGL. Owner operator (SITL lidar model) / `sitl`.

https://docs.px4.io/main/en/flying/terrain_following_holding

## SITL params we must set (or refuse)

Do **not** invent defaults. Values marked unknown stay unknown until QGC on the SIH image.

| Param | Value | Why | URL |
|---|---|---|---|
| `COM_RC_IN_MODE` | **do not** set `4` (Disable manual control) | Offboard page allows no-RC. Project forbids it. Exact non-4 enum for SIH-without-radio: **unknown**, owner operator. | https://docs.px4.io/main/en/flight_modes/offboard |
| `COM_RCL_EXCEPT` | **do not** set bit `2` (ignore RC loss in Offboard) | RC loss must still failsafe. | https://docs.px4.io/main/en/flight_modes/offboard |
| `COM_OF_LOSS_T` | **unknown** seconds (keep short). Owner operator | Timeout then `COM_OBL_RC_ACT`. PX4 min proof-of-life 2 Hz. | https://docs.px4.io/main/en/flight_modes/offboard |
| `COM_OBL_RC_ACT` | Position or Return — **not** a spray-holding mode. Exact enum **unknown**, owner operator | Mode after Offboard loss. Pump 0 first. | https://docs.px4.io/main/en/flight_modes/offboard |
| `MAN_OVERRIDE_SPD` | leave enabled (do not set `-1`) | Stick steals to Position (PX4 v1.18). | https://docs.px4.io/main/en/flight_modes/offboard |
| `NAV_RCL_ACT` | Return or Land — never Disabled | RC loss. | https://docs.px4.io/main/en/config/safety |
| `NAV_DLL_ACT` | Return or Land — never Disabled | Laptop disconnect. | https://docs.px4.io/main/en/config/safety |
| `GF_ACTION` | Hold or Return — not None, not Terminate | Fence breach. Pump off. | https://docs.px4.io/main/en/config/safety · https://docs.px4.io/main/en/flying/geofence |
| `COM_PREARM_MODE` | **unknown**, owner operator | Non-motor outputs can move in prearm. Pump DIS must still be off. | https://docs.px4.io/main/en/advanced_config/parameter_reference.html#COM_PREARM_MODE |

Arm/takeoff: RC-first = pilot Position/Altitude takeoff, then dashboard Offboard after the 2 Hz stream is live. Dashboard-first = same stream, then Action takeoff/Offboard. Both legal in PROJECT.md. RC override stays available.

Hardware later: Pi USB CDC (`SYS_USB_AUTO=2`), not 14540 on the Kakute.
