# weed-spray BOM vs $500

**Priced:** 2026-08-30 MDT. Goods from live US pages that day. Ship/tax are EST. No checkout.

Source CSV: `bom/current.csv` (sum below matches that file).

## Total vs $500

| Bucket | USD |
|---|---:|
| Parts (goods only) | 731.85 |
| Shipping EST (Holybro $25 + GetFPV $10; Amazon $0) | 35.00 |
| Tax EST (8% Amazon + GetFPV; not a checkout quote) | 48.43 |
| **All-in EST** | **815.28** |
| Hard cap | 500.00 |
| **Gap** | **315.28 over** |

6–12 inch lidar-hold is possible on this airframe (S500 + 2212 920KV 4S + TFmini-S 0.1 m min + PMW3901). It is **not possible inside $500** without dropping a required item. Gap reported instead of deleting rangefinder or flow.

## What you must not cut

- Downward rangefinder (TFmini-S)
- Optical flow (Holybro PMW3901)
- ELRS TX + RX (Pocket + RP1)
- PX4 FC (Kakute H7 Mini)
- 12V pump (CrocSee)

## What I would cut last

1. Handheld ELRS TX
2. Kakute H7 Mini
3. TFmini-S / PMW3901
4. 4S propulsion

Cut first (still over cap): Pi 4 path, S500→F450, M10→cheap GPS, spare LiPo, second Matek if a smaller 12 V buck is found.

**The cap does not close today.**

## Top 3 cost drivers (parts)

1. Companion path (Pi 4 + SD + camera + 5.2 V BEC) — $163.72
2. Propulsion (frame, motors, ESC, props, 2×4S, charger) — $223.94
3. ELRS Pocket TX — $79.99

## UART map (Kakute H7 Mini)

Signed with @px4 / @hardware. USB MAVLink is STM32 CDC, not USART1. Keep Kakute. Do not buy Pixhawk 6C Mini for this.

Kakute pinout: https://docs.px4.io/main/en/flight_controller/kakuteh7mini  
TFmini UART-only: https://docs.px4.io/main/en/sensor/tfmini  
PMW3901 UART: https://docs.px4.io/main/en/sensor/pmw3901

| Port | Device | PX4 |
|---|---|---|
| USB CDC | Raspberry Pi 4 MAVLink | `SYS_USB_AUTO=2` (owner @px4) |
| UART1 TELEM1 | Benewake TFmini-S | `SENS_TFMINI_CFG` |
| UART2 TELEM2 | Holybro PMW3901 | `SENS_TFLOW_CFG` |
| UART3 | debug | leave it |
| UART4 GPS1 | Holybro M10 | GPS1 |
| UART6 RC | ELRS RP1 V2 CRSF | RC |
| UART7 | DShot telem RX-only | unused (PWM ESCs) |
| I2C | M10 IST8310 compass only | not TFmini |

## Conflicts (do not ignore)

- **Old I2C TFmini plan is withdrawn.** PX4 `tfmini` is UART-only.
- **Pump vs 4S:** CrocSee 9–14 V. Do not clip to raw 4S. Second Matek 12S Pro BEC jumpered 12 V is in the CSV (GetFPV In Stock, $24.99). Matek page: VIN>=14 V for stable 12 V. 4S empty ~13.2 V may sag under that dropout.
- **USB yank:** VBUS cut; pump must go off. Owner @hardware / @px4.
- **Motors 2–4S.** No 6S pack.
- **OPTO ESCs have no BEC.** Kakute 5 V/2 A feeds FC+sensors. Pi uses the 5.2 V Matek. Pump uses the 12 V Matek.
- **Pocket 2×18650:** unknown, owner parts.
- **Holybro China DAP ship:** EST $25. Tariff unknown, owner parts.

## Substitutions not used

- Pixhawk 6C Mini $130.99: extra UARTs, not needed after USB CDC.
- SpeedyBee F405 V4: not a PX4 target.
- Matek H743-MINI: RMRC unavailable 2026-08-30.
- TF-Luna: cheaper, blind below ~8 in.
- VL53L1X I2C $14.99: PX4 table, not TF-Luna class, bad outdoor 6 in.
- ESP32-S3 CAM $19.95: RTSP yes, YOLO-on-laptop will hate MJPEG. CSV stays Pi 4 until operator picks.

## Approval

Stop. No carts, no checkout, no vendor email.
