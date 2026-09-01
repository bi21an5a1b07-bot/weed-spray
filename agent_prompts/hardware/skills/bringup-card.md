Save this as a skill named **bringup-card**. Enable it on the `hardware` Bot.

When to use: operator has a BOM, received a package, or asks how to wire lidar/pump/companion.

Inputs: bom/current.csv, px4/actuators.md, PROJECT.md.

Steps:

1. Map each BOM line to a connector (power, UART, PWM, USB, WiFi).
2. Update wiring.md. Pump path must include a way to leave it disconnected.
3. Update first-flight.md in three phases: bench no-props, maiden no-spray, spray over a tray at 6–12 in.
4. Call out prop-in-grass and wet electronics risks.

Validate: no “now arm it” without RC-in-hand language. Voltages consistent with the BOM.

Approval: any change to a live vehicle.
