# weed-spray first-flight card

Operator-owned. This bot does not arm, does not apply bench voltage, and does not pulse the pump.

Locked: RC in the pilot’s hands whenever motors can spin. Maiden with the pump electrically disconnected. Vinegar/salt only. **6–12 inch hover is a later flight, not the first hover.** See `PROJECT.md` and `SAFETY.md`.

`$500` cap is currently over (`bom/cap.md`). That does not block this card. Pump is Kakute M5 / Actuator Set 1, failsafe PWM low (`px4/actuators.md`).

## Phase 1 — bench, no props

- [ ] Smoke-stop you confirmed: LiPo bag, extinguisher, pack unplug you can hit with one hand.
- [ ] Props **off**. Tank empty. Vinegar not on the aircraft.
- [ ] Pump 12 V fused XT60 / bullet **open**. Wiring matches `hardware/wiring.md`.
- [ ] Pi on Matek 5.2 V only. Kakute 5 V feeds FC / GPS / flow / lidar / RP1 only.
- [ ] USB pigtail: VBUS cut (meter open), GND common, strain-relieved to the plate. Pi sees `/dev/ttyACM0`.
- [ ] Yank USB on the bench: M5 / pump gate goes **low**. Pump lead still open.
- [ ] Pump 12 V is the **second** Matek, jumper 12 V. Pi is the 5.2 V Matek. Do not clip the pump to 4S.
- [ ] Kakute: PX4 bootloader, then PX4 v1.14+ / main (ships Betaflight).
- [ ] Pocket TX: 2×18650 (not in BOM), RP1 bound, T-antenna on U.FL. RC in hand for every powered check that could spin motors (motors still prop-less here).
- [ ] First pack plug is yours. Expect FC boot, no smoke, BEC not hot.
- [ ] Pi Cam3 can stream a few seconds without Kakute 5 V dipping.
- [ ] QGC sees RC. Failsafe = motor PWM idle, M5 / pump gate **low**.
- [ ] GPS / compass / PMW3901 talk. TFmini-S is on UART1. If no `DISTANCE_SENSOR`, that blocks Phase 3, not this bench.

Grass / wet: do not run this bench over wet turf. No spray on the plate.

## Phase 2 — maiden, no spray (not 6–12 in)

First hover is a normal outdoor hop, **well above grass**, pump still electrically open. Not a lidar-hold. Not a spray.

- [ ] Pump 12 V lead **open** (unplugged or fuse out). Not software off.
- [ ] Geofence = this yard. VLOS. No people, pets, neighbor, garden beds.
- [ ] Short grass or a hard pad. 1045 props will eat tall grass and bury CF gear.
- [ ] Fresh 4S. 2200 mAh is short. Two minutes, then land.
- [ ] RC in hand. If you choose to arm, that choice is yours with the radio in your hands. This card does not arm.
- [ ] After landing: pack off. Inspect FET, BEC, belly sensors. Still dry.

Abort: BEC/FET too hot, Pi or Kakute brown-out, no RC, anyone in the box, props in grass.

## Phase 3 — spray over a tray at 6–12 in (later flight)

Do this only after Phase 2 was boring. Needs a live rangefinder. GPS will not hold 6–12 in.

- [ ] TFmini-S actually publishing distance on UART1. If USB CDC is down, do not spray (pump must fail off). Do not drop the rangefinder.
- [ ] Second Matek jumpered 12 V. Pump lead connected. **Water first**, over a bucket / tray. Vinegar/salt only after a water pulse works. No herbicide.
- [ ] First pulse: props **off**, aircraft over the tray, human confirm, ~0.75 s. Watch Kakute 5 V and FET temp.
- [ ] Flush. Then a short 6–12 in hover **over the tray**, RC in hand, human-confirmed pulse, land, flush.
- [ ] Wet electronics: if the mister wets lidar, flow, Kakute, or the Pi, pack off, dry, do not fly. Salt pits steel; wetted path is HDPE / brass / silicone.
- [ ] Pump off on failsafe, RC loss, laptop disconnect, USB unplug, geofence breach. If M5 does not drop, do not spray.

Prop-in-grass at 6–12 in: CF gear can sink, 10 in props hit turf, lidar sees grass blades as altitude. Keep the tray, keep the hover over short grass or the tray lip, not in the weeds.

## Abort (any phase)

Unplug the pack: brown-out, no RC, no geofence, spray on a lens, FET/BEC too hot, people in the box.
