# weed-spray PX4 parameters

**Date:** 2026-08-30. Sources fetched this date.  
Do not arm, Offboard, or send MAVLink from this file. Values marked **unknown** are not guesses.

Kakute H7 Mini: https://docs.px4.io/main/en/flight_controller/kakuteh7mini  
Param links: `https://docs.px4.io/main/en/advanced_config/parameter_reference.html#NAME`

**SIH (`sihsim_quadx`) has IMU/GPS/baro/mag, not lidar, not optical flow.** https://docs.px4.io/main/en/simulation/#simulator-comparison  
Rangefinder + flow rows are **hardware-only**. Do not copy them into SIH.

## UART map (hardware, USB cable signed)

`hardware/wiring.md`: Pi USB-A → Kakute USB-C, VBUS cut. TFmini on UART1. I2C = compass only.

| UART / bus | Use | Docs |
|---|---|---|
| UART1 | TFmini-S `SENS_TFMINI_CFG` | https://docs.px4.io/main/en/sensor/tfmini |
| UART2 | PMW3901 `SENS_TFLOW_CFG` (disable `MAV_1_CONFIG` first) | https://docs.px4.io/main/en/sensor/pmw3901 |
| UART3 | debug — leave it | https://docs.px4.io/main/en/flight_controller/kakuteh7mini |
| UART4 | M10 GPS | https://docs.px4.io/main/en/gps_compass/ |
| UART6 | ELRS CRSF `RC_CRSF_PRT_CFG` (needs `crsf_rc` build) | https://docs.px4.io/main/en/telemetry/crsf_telemetry |
| UART7 | unused (PWM ESCs, no DShot telem) | kakuteh7mini |
| USB CDC | Pi companion. `SYS_USB_AUTO=2` | https://github.com/PX4/PX4-Autopilot/pull/22234 |
| I2C | IST8310 mag only. **Not** TFmini (PX4 `tfmini` is UART-only) | https://docs.px4.io/main/en/sensor/tfmini |

## Table

| Param | Value | Why | SITL vs HW | URL |
|---|---|---|---|---|
| `COM_RC_IN_MODE` | do **not** set `4` | Keep RC. SIH-without-radio enum: **unknown**, owner operator | Both | https://docs.px4.io/main/en/flight_modes/offboard |
| `COM_RCL_EXCEPT` | do **not** set bit `2` | RC loss still counts in Offboard | Both | https://docs.px4.io/main/en/flight_modes/offboard |
| `COM_OF_LOSS_T` | **unknown** (keep short) | Offboard proof-of-life timeout | Both | https://docs.px4.io/main/en/flight_modes/offboard |
| `COM_OBL_RC_ACT` | Position or Return. Exact enum **unknown** | After Offboard loss. Pump 0 | Both | https://docs.px4.io/main/en/flight_modes/offboard |
| `MAN_OVERRIDE_SPD` | not `-1` | Stick → Position | Both | https://docs.px4.io/main/en/flight_modes/offboard |
| `NAV_RCL_ACT` | Return or Land, never Disabled | RC loss | Both | https://docs.px4.io/main/en/config/safety |
| `NAV_DLL_ACT` | Return or Land, never Disabled | Laptop loss | Both | https://docs.px4.io/main/en/config/safety |
| `GF_ACTION` | Hold or Return, not None/Terminate | Fence. Pump off | Both | https://docs.px4.io/main/en/config/safety |
| `COM_PREARM_MODE` | **unknown** | Non-motor outputs may move in prearm. Pump DIS = off | Both | https://docs.px4.io/main/en/advanced_config/parameter_reference.html#COM_PREARM_MODE |
| `PWM_*_FUNC5` | `301` Peripheral via Actuator Set 1 | Pump. MAIN vs AUX prefix **unknown** until QGC | HW (SITL: spare virtual ch if exposed) | https://docs.px4.io/main/en/payloads/generic_actuator_control |
| `PWM_*_DIS5` / `FAIL5` | MOSFET off. µs **unknown**, owner `hardware` | Default + failsafe low. Never Parachute (`401`) | HW | https://docs.px4.io/main/en/config/actuators · https://docs.px4.io/main/en/config/safety |
| `SYS_USB_AUTO` | `2` always start MAVLink | Pi USB CDC | HW | https://docs.px4.io/main/en/advanced_config/parameter_reference.html#SYS_USB_AUTO |
| `USB_MAV_MODE` | Onboard | Companion profile | HW | parameter reference |
| `MAV_0_CONFIG` | not TELEM1 | UART1 is TFmini | HW | https://docs.px4.io/main/en/peripherals/mavlink_peripherals |
| `MAV_1_CONFIG` | Disabled | UART2 is flow | HW | https://docs.px4.io/main/en/peripherals/serial_configuration |
| `SYS_HAS_MAG` | `1` once IST8310 is on I2C | Kakute has no internal mag | HW | https://docs.px4.io/main/en/flight_controller/kakuteh7mini |
| `GPS_1_CONFIG` | GPS 1 / UART4 | M10 | HW | https://docs.px4.io/main/en/gps_compass/ |
| `SENS_TFMINI_CFG` | TELEM1 / UART1 | TFmini UART-only. **Hardware-only. SIH: omit.** | HW | https://docs.px4.io/main/en/sensor/tfmini |
| `SENS_TFLOW_CFG` | TELEM2 (`102`) | PMW3901 UART. **Hardware-only. SIH: omit.** | HW | https://docs.px4.io/main/en/sensor/pmw3901 |
| `SENS_FLOW_ROT` | match mount (notch aft). Exact **unknown** until mounted | HW | HW | https://docs.px4.io/main/en/sensor/pmw3901 |
| `EKF2_OF_CTRL` | enable when flow+range exist | Flow needs valid range. **Hardware-only. SIH: omit.** | HW | https://docs.px4.io/main/en/sensor/optical_flow |
| `EKF2_RNG_CTRL` | **unknown** (`1` vs `2`). Owner operator after live `DISTANCE_SENSOR` | **Hardware-only. SIH: omit.** | HW | https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf.html |
| `EKF2_HGT_REF` | **unknown** | GNSS for scan vs range for spray. **Hardware-only.** | HW | https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf.html |
| `MPC_ALT_MODE` | `2` only in Position/Altitude | Terrain hold **not documented for Offboard** | Both (no effect without range) | https://docs.px4.io/main/en/flying/terrain_following_holding |
| `RC_CRSF_PRT_CFG` | UART6 | ELRS. Needs custom `crsf_rc` image | HW | https://docs.px4.io/main/en/telemetry/crsf_telemetry |

PWM ESCs on M1–M4 (not DShot): https://docs.px4.io/main/en/config/actuators

## Open

1. MAIN vs AUX tab on Kakute — owner operator.  
2. DIS/FAIL µs for IRLZ44N — owner `hardware`.  
3. `set_actuator(1, 0)` vs `-1` — owner operator (SITL) then `hardware`.  
4. 12 V rail is a second Matek BEC (`parts`). 4S empty sag vs 14 V dropout — owner `hardware`.  
5. Offboard AGL at 0.15–0.30 m — owner operator; SIH will fail that step without `DISTANCE_SENSOR`.
