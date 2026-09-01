Produce the first PX4 implementation checklist for weed-spray.

Read `/workspace/weed-spray/PROJECT.md` and `SAFETY.md`.

Outcome: three markdown files under `/workspace/weed-spray/px4/` covering (1) parameters for a small quad with downward lidar and optical flow, (2) 12V pump as a PX4 actuator that defaults off, (3) Offboard/goto sequence for scan-then-confirmed-visit, including 6–12 inch AGL hold.

Sources: current PX4 documentation. Link every parameter.

Constraints: SITL on Docker UDP 14540 is the first target. Do not assume Gazebo camera is required. Do not send commands to a vehicle.

Deliverable: write the three files, then a one-page summary in chat with open questions (UART for lidar vs flow vs GPS). Stop for review.
