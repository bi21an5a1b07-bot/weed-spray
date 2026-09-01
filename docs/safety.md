# Safety

Contract: `agent_prompts/_shared/SAFETY.md`, `bot_files/faa_current.md`.

## Software must keep

- Human confirm before every spray. Inject ≠ confirm.
- RC transmitter in the pilot’s hands whenever motors can spin (hardware). SITL may use dashboard-first takeoff; do not disable RC loss handling in PX4 params.
- Geofence stay-on-turf. Does not replace VLOS or a people check.
- Pump commanded **off** on kill, RC loss, Offboard loss, geofence, disconnect, RTL, people/pets hold, process shutdown.
- Grok Bots never arm, Offboard, or pulse a real pump.

Dashboard: **Kill (pump off)** and **People/pets — hold**. `GET /preflight` repeats these reminders.

## FAA / EPA (not legal advice)

- Recreational 49 USC 44809 is a limited exception. FAA lists agricultural spraying as a non-recreational example.
- Dispensing from an aircraft can engage **14 CFR Part 137** (purpose-based; includes substances intended for pest control / weeds). Grocery vinegar is **not** documented as a free pass.
- Registered acetic-acid herbicides often **ban aerial application**; FIFRA label-is-the-law.
- Ready-to-fly mass will almost certainly exceed 250 g → recreational registration + Remote ID if flying 44809.
- SITL and dry runs do **not** authorize a spray flight.

Primary URLs are listed in `bot_files/faa_current.md`.
