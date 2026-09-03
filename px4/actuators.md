# weed-spray pump actuator

**Date:** 2026-08-30. Sources fetched this date.  
This Bot does not send MAVLink, arm, or pulse a pump.

Wiring: `/workspace/weed-spray/hardware/wiring.md` (USB cable signed: Pi USB-A to Kakute USB-C, VBUS cut). Pump 12 V is a second Matek BEC jumpered 12 V (`parts` CSV). Maiden: pump lead open. 4S sag vs Matek 12 V dropout is a rail issue, not a MAVLink mapping.

Default: **OFF**. Hardware 10 kΩ pull-down + software 0. Never latch ON. Do not assign **Parachute**.

## Command (SITL and hardware)

| Item | Contract |
|---|---|
| MAVLink | `MAV_CMD_DO_SET_ACTUATOR` (187) https://mavlink.io/en/messages/common.html#MAV_CMD_DO_SET_ACTUATOR |
| Mapping | `param1` = Peripheral via Actuator Set 1. `param2`–`param6` NaN. `param7` = 0. https://docs.px4.io/main/en/payloads/generic_actuator_control |
| Scale | **[-1, 1]**. ON = `1`. OFF = `0` (**proposed**; confirm which of `0` / `-1` is MOSFET low). |
| MAVSDK | `await drone.action.set_actuator(1, value)` — index **starts at 1**. Same command under the hood. http://mavsdk-python-docs.s3-website.eu-central-1.amazonaws.com/plugins/action.html#mavsdk.action.Action.set_actuator |
| Pulse | **0.75 s in the app** (`asyncio.sleep`). PX4 does not dwell. Then `set_actuator(1, 0)`. |
| Confirm | Human confirm on the laptop. Software must not auto-spray. |

```
set_actuator(1, 1.0)
sleep 0.75
set_actuator(1, 0.0)
finally: set_actuator(1, 0.0)
```

## Force OFF

App commands `set_actuator(1, 0)` on: kill, RC loss, Offboard loss, geofence, laptop disconnect, RTL, exception.  
PX4 DIS/FAIL PWM on that channel must also be MOSFET low so a dead app cannot leave the gate high.

https://docs.px4.io/main/en/config/safety  
https://docs.px4.io/main/en/flight_modes/offboard

## SITL vs hardware pin

PX4 generic-actuator docs show a **Pixhawk AUX** example (`AUX5` = Actuator Set 1). https://docs.px4.io/main/en/payloads/generic_actuator_control

| Target | Physical pin | Function |
|---|---|---|
| **SITL** (`sihsim_quadx`) | none (virtual channel) | Assign **Peripheral via Actuator Set 1** on a spare SITL output if the Actuators tab exposes one. Watch `actuator_outputs` / QGC sliders. SIH has no MOSFET. |
| **Kakute H7 Mini** (this BOM) | **M5 PWM** to IRLZ44N gate | Kakute has **no IO MCU**. M1–M8 are FMU pads. QGC tab name MAIN vs AUX: **unknown**, owner operator on first connect. `PWM_MAIN_FUNC5` or `PWM_AUX_FUNC5` = **301**. https://docs.px4.io/main/en/flight_controller/kakuteh7mini |
| **Pixhawk-class later** | unused **AUX** pin | Same function 301 on that AUX. Not this airframe unless `parts` swaps FC. |

DIS/FAIL µs that hold the IRLZ44N off: **unknown**, owner `hardware` (meter, pump disconnected).

https://docs.px4.io/main/en/config/actuators  
https://github.com/PX4/PX4-Autopilot/blob/main/src/lib/mixer_module/output_functions.yaml
