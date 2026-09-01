# Grok Bot computer layout

Durable files live here. Do not keep project state only in chat.

```text
/workspace/weed-spray/
  PROJECT.md              # spec (copied from repo)
  SAFETY.md
  WORKSPACE.md
  bom/
    current.csv           # live BOM
    cap.md                # $500 rollup + gap
    carts.md              # draft carts, no checkout
  px4/
    parameters.md
    actuators.md
    offboard.md
  weeds/
    sources.md
    class-map.md
    notes.md
  sitl/
    loop.md
    last-run.md
    summaries/            # one markdown per run (sitl owns this; no logs Bot)
  hardware/
    wiring.md
    first-flight.md
  faa/
    current.md
```

When handing off to another Bot, write the file first, then point at the path. Do not paste large tables only in chat.
