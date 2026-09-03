# weed-spray — locked product spec

Authoritative for every Grok Bot on this project. If a chat disagrees with this file, this file wins until the operator edits it.

## What we are building

Laptop ground station talks to a backyard quad over MAVLink (PX4). A camera on the drone streams WiFi RTSP to the laptop. YOLO on the laptop finds dandelion, clover, thistle, and mallow (mallow includes ground ivy). The drone scans the whole lawn, the operator confirms targets, then the drone visits each confirmed weed, hovers 6–12 inches AGL using a downward rangefinder, and pulses a 12V pump of household vinegar/salt.

## Software (this repo)

- Path: `/home/behmann/src/grok/drone_control` (WSL). Windows: `\\wsl$\Ubuntu\home\behmann\src\grok\drone_control`
- App name: weed-spray / backyard-spot-spray
- New repo. Borrow patterns from `/home/behmann/src/ai_drone_fleet`; do not fork it
- Python + TypeScript web dashboard. No ROS. No cloud in the app. Localhost/LAN only
- Flight stack: PX4, MAVLink. Prefer MAVSDK-Python
- Dev: Docker PX4 SITL on this WSL machine first, hardware later
- Python 3.11 via uv (host Python is 3.13)
- SITL MAVLink: UDP 14540
- Vision: local YOLO on the RTX 4090, not a cloud LLM in the inner loop
- Companion Pi code: protocol + mock in this repo now; real image when parts exist

## Mission

1. Operator sets a typed rectangle geofence in SITL (walk-the-fence GPS later)
2. Arm/takeoff: either RC-first or dashboard-first (operator choice)
3. Drone lawnmower-scans the box
4. Laptop records detections (classes: `dandelion`, `clover`, `thistle`, `mallow`)
5. Operator confirms a subset
6. Drone visits each confirmed target, lidar-hold 6–12 in AGL, pulse pump, next
7. RTL / land. Pump off on any failsafe, disconnect, or geofence breach
8. RC transmitter in the pilot’s hands whenever motors can spin

## Yard and payload

- US hobby backyard, visual line of sight, under 5,000 sq ft
- Open lawn, fence, maybe a tree or two. Stay on turf inside the geofence
- Spray: household vinegar/salt, 12V mini pump + nozzle. Default pulse 0.75 s, configurable
- Not commercial herbicide in v1
- Human confirms every spray. Software must not auto-spray

## Hardware budget

- **$500 USD must buy the entire flyable spray drone** (frame, FC, motors, ESCs, GPS, flow, rangefinder, ELRS TX+RX, battery, charger, companion, camera, tank, pump, wiring)
- Laptop / this DevStation is owned and not in the $500
- GPS cannot hold 6–12 inches. A cheap downward lidar/sonar (TF-Luna class or better) is mandatory for that requirement
- Optical flow (or equivalent GPS-denied aid) is required near the ground
- Companion: WiFi RTSP to the laptop (Pi Zero 2W class or cheaper that actually streams)
- If the BOM cannot close, say so with a dollar gap. Do not silently drop the rangefinder

## Machine that runs the app

- WSL2 Ubuntu 22.04, i9-14900KF, RTX 4090, ~25 GB RAM, Docker 29
- No USB serial and no `/dev/video` inside WSL. SITL uses UDP. Real radios need a Windows helper later
- Outdoor cheap laptop is a later portable GCS; v1 is developed here

## Grok Bot vs Grok Build vs Grok API

- **Grok Build** (this WSL repo): writes and runs the software
- **Grok API**: optional second look at a still crop, never the 30 fps detector
- **Grok Bot** (these profiles): research, BOM, datasets, checklists, log triage. No live flight control
