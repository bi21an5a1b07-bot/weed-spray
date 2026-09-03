# bot_files ingest

Grok Bot writes contracts on a cloud VM. They only affect this repo after the operator copies them into `bot_files/`. When a file is **added or changed**, implement it. Do not re-litigate unchanged files.

A Linux crontab runs `scripts/bot_files_cron.sh` every 15 minutes (no Grok). If `var/bot_files-pending` exists, ingest it in a session.

Detect deltas by hand:

```bash
uv run python scripts/bot_files_delta.py
```

Exit 0 = nothing to do (or first-run baseline was recorded). Exit 1 = process `added` / `changed` / `removed`, then:

```bash
uv run python scripts/bot_files_delta.py --commit
```

Then `make check`.

## Route by filename

| File | Action |
|---|---|
| `loop.md` / `sitl_loop.md` | Ports, compose images, `accept.py` steps, dashboard routes |
| `sitl_template.md` | `GET /run-log` + `sitl/summaries/_template.md` |
| `px4_actuators.md` | Pump `set_actuator` index/on/off/pulse; no Parachute |
| `px4_offboard.md` | Connect `udpin://0.0.0.0:14540`, scan-then-descend; **do not invent PX4 params** |
| `px4_parameters.md` | Document only; unknown enums stay unknown |
| `weeds_class-map.md` | `dandelion=0 clover=1 thistle=2 mallow=3`; update `classes.py` + `weeds.yaml` + tests |
| `weeds_notes.md` | Labeling rules; do not add classes beyond the map |
| `weeds_sources.md` | `weed-spray-train --list-sources`; **never auto-download** |
| `faa_current.md` | `GET /preflight` reminders only; not legal advice |
| `parts_cap.md` / `parts_current.csv` | Report $ gap; **do not drop TFmini or PMW3901** |
| `hardware_wiring.md` / `hardware_first-flight.md` | `docs/hardware.md`; do not arm hardware |

Unknown new names: read the file, classify as flight / vision / safety / research, implement or document, do not ignore.

## Still never

Auto-confirm spray. Treat SIH local `z` as AGL. Auto-download weed archives. Write `COM_RCL_EXCEPT` bit 2 or disable `NAV_RCL_ACT` unless the offboard contract now states a sourced value.
