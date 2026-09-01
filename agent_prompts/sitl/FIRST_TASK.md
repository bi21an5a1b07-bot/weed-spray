Write the SITL acceptance loop for weed-spray without starting any containers.

Read `/workspace/weed-spray/PROJECT.md`, `SAFETY.md`, and `px4/offboard.md` if present.

Outcome:

1. `/workspace/weed-spray/sitl/loop.md` — every process (PX4 Docker, backend, mock RTSP, dashboard, YOLO worker), ports (include UDP 14540), and a step-by-step pass/fail script: connect, typed geofence box, scan, inject or detect boxes, confirm subset, visit, 6–12 in hover, 0.75 s pump pulse, RTL, pump-off on kill.
2. `/workspace/weed-spray/sitl/summaries/_template.md` — setup, detections by class, confirms, hover 6–12 in stats, pump pulses vs 0.75 s, failsafes, geofence, defects, plus which PX4 ulog topics or dashboard JSON keys Grok Build must log.

Constraints: this cloud computer is not the WSL box. Do not use local computer. Do not assume Gazebo camera; mock RTSP from a file is the v1 video source. There is no `logs` Bot.

Deliverable: write both files, then 10 bullets in chat of what Grok Build still has to implement. Stop.
