# Getting started

## Requirements

- WSL2 Ubuntu with Docker, `uv`, Node.js, `ffmpeg`
- Optional: NVIDIA GPU for later YOLO training (`uv sync --extra yolo`)

## Install

```bash
cd /home/behmann/src/grok/drone_control
uv sync --extra dev
(cd dashboard && npm install)
```

## SITL (software-in-the-loop)

```bash
make sitl                 # PX4 SIH + MediaMTX + ffmpeg file RTSP
uv run weed-spray-vision  # injector :8090
uv run weed-spray         # backend  :8000
(cd dashboard && npm run dev)  # UI :8080
```

Open http://127.0.0.1:8080

1. Connect
2. Set fence (meters from home)
3. Inject detections (`POST /detections/inject` or wait for harness)
4. Scan (dashboard-first in SITL)
5. Select a subset → Confirm
6. Visit confirmed
7. Kill (pump off)

## Tests

```bash
uv run pytest -q          # unit + API integration (fake vehicle, no PX4)
make check                # ruff lint + format --check + pytest
uv run weed-spray-accept  # live 10-step loop.md grade (needs SITL + apps)
```

See [testing.md](testing.md). Commands: [cli.md](cli.md). Function map: [code-reference.md](code-reference.md).

## What not to expect from SIH

PX4 SIH has no downward lidar. Hover AGL is logged as `missing` and accept step 7 **fails** until `DISTANCE_SENSOR` exists. Do not treat GPS / local `z` as AGL.
