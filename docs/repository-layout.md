# Repository layout

```
drone_control/
  compose.yaml              # PX4 SIH + MediaMTX + ffmpeg only
  pyproject.toml            # uv package + [tool.ruff] + pytest
  GROK.md                   # Grok Build instructions (read this)
  AGENTS.md                 # pointer to GROK.md (auto-loaded by Grok TUI)
  Makefile                  # sitl / backend / vision / dashboard / accept / lint / check
  README.md                 # short start; points here
  docs/                     # this documentation
  src/weed_spray/
    __init__.py
    backend/                # FastAPI GCS + MAVSDK
      config.py             # WEED_* settings
      models.py             # HTTP + run-log Pydantic models
      geo.py                # NED ↔ WGS84, lawnmower
      vehicle.py            # MAVSDK wrapper
      mission.py            # scan → confirm → visit FSM
      main.py               # FastAPI routes :8000
    vision/
      classes.py            # frozen dandelion/clover/thistle
      main.py               # injector :8090
      train.py              # optional YOLO CLI
    harness/
      accept.py             # live loop.md grader
  dashboard/src/            # Vite + React :8080
  tests/
    fakes.py                # FakeVehicle
    conftest.py             # reset injector boxes
    unit/                   # no HTTP PX4
    integration/            # ASGI HTTP + FakeVehicle
  weeds/
    weeds.yaml              # nc=3 names
    inbox/                  # operator lawn photos (later)
    dataset/images/{train,val}
  sitl/
    mediamtx.yml            # RTSP path cam
    summaries/_template.md  # run-log contract
  media/                    # RTSP file (smoke.mp4 gitignored)
  bot_files/                # downloaded Grok Bot contracts
  agent_prompts/            # Bot profiles for the Windows Grok Bot app
  var/                      # last-run.md, yolo runs (gitignored)
```

Grok Bot cloud files are **not** this tree until copied into `bot_files/`. Function docs: [code-reference.md](code-reference.md). Commands: [cli.md](cli.md).
