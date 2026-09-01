Save this as a skill named **px4-hover-pump-checklist**. Enable it on the `px4` Bot.

When to use: operator asks how to hover low, map a pump, set Offboard, geofence, or failsafes in PX4.

Inputs: PROJECT.md, optional bom/current.csv (which lidar, FC, flow).

Steps:

1. Identify FC, lidar model, flow, and pump voltage from the BOM if present.
2. Look up current PX4 docs for that rangefinder and flow (not a cached param list).
3. Update `px4/parameters.md`, `actuators.md`, `offboard.md`.
4. Explicitly state how the pump is commanded from a laptop via MAVLink and how it is forced off on failsafe.
5. List SITL vs hardware differences (simulated distance sensor vs real UART).
6. Open questions at the bottom, each with an owner (`parts`, `hardware`, operator).

Validate: every parameter has a docs URL. Pump default is off. No live vehicle commands.

Approval: stop after writing files.
