# Hardware (target airframe)

Contracts: `bot_files/parts_current.csv`, `parts_cap.md`, `hardware_wiring.md`, `hardware_first-flight.md`, `px4_parameters.md`, `px4_actuators.md`.

This software does not power or arm hardware. Maiden: pump lead **open**.

## Stack (2026-08-30 BOM)

- Frame: S500. FC: Holybro Kakute H7 Mini (PX4; flash bootloader from Betaflight).
- Companion: Raspberry Pi 4, USB CDC to Kakute, **VBUS cut**. `SYS_USB_AUTO=2` on hardware. Not UDP 14540 on the Kakute.
- TFmini-S on **UART1** (`SENS_TFMINI_CFG`). PX4 `tfmini` is UART-only; I2C plan withdrawn.
- PMW3901 on **UART2**. GPS M10 on UART4. ELRS RP1 CRSF on UART6.
- Pump: CrocSee 12 V from a **second** Matek BEC jumpered 12 V (not raw 4S). MOSFET IRLZ44N gate from Kakute **M5** = Peripheral via Actuator Set 1 (`set_actuator(1)`). Gate pulldown default OFF. Do not assign Parachute.
- Pi 5.2 V from the **first** Matek. Kakute 5 V BEC is FC/sensors only.

All-in estimate ~$815 vs $500 cap. Lidar and flow were not dropped.

## First flight (operator-owned)

1. Bench, no props, pump XT60 open.
2. Maiden hover well above grass, pump still open. Not 6–12 in.
3. Later: live TFmini, water over a tray, then vinegar. RC in hand.

See `bot_files/hardware_first-flight.md`.
