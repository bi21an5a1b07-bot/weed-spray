# CLI, Makefile, and package scripts

Host tools (Python 3.11, uv, Node 26) are pinned in `mise.toml`. After clone: `mise trust && mise install && mise run install`.

Python entry points are declared in `pyproject.toml` `[project.scripts]`. After `uv sync` they are available as `uv run <name>`.

## Python CLIs

| Command | Module | What it does |
|---|---|---|
| `uv run weed-spray` | `weed_spray.backend.main:run` | FastAPI GCS on `WEED_HTTP_HOST`:`WEED_HTTP_PORT` (default `127.0.0.1:8000`) |
| `uv run weed-spray-vision` | `weed_spray.vision.main:run` | Injector on `127.0.0.1:8090` |
| `uv run weed-spray-accept [--out PATH]` | `weed_spray.harness.accept:main` | Live 10-step `loop.md` grade; writes `var/last-run.md` |
| `uv run weed-spray-train` | `weed_spray.vision.train:main` | Ultralytics train; exit 2 if dataset empty |
| `uv run weed-spray-train --list-sources` | same | Print `bot_files/weeds_sources.md`; never downloads |
| `uv run pytest -q` | pytest | Unit + integration; `FakeVehicle`; no PX4 |
| `uv run ruff check src tests` | ruff | Lint (`[tool.ruff]` in `pyproject.toml`) |
| `uv run ruff format src tests` | ruff | Format in place |
| `make check` | ruff + pytest | Lint, format `--check`, then pytest |
| `uv run python scripts/bot_files_delta.py` | helper | Exit 1 if `bot_files/` added/changed/removed |
| `uv run python scripts/extract_clip_inbox.py` | helper | 1 fps JPEGs from `media/backyard_weeds.MOV` → `weeds/inbox/backyard_weeds/` |
| `uv run python scripts/promote_inbox.py` | helper | Copy boxed inbox stills into `weeds/dataset/` (split by image) |
| `mise run bot-files` | same | Periodic ingest detector |

User crontab (`*/15`) runs `scripts/bot_files_cron.sh` on this WSL box — hash only, no LLM. Snapshot: `var/bot_files-state.json`. Pending delta: `var/bot_files-pending`. Log: `var/bot_files-cron.log`. Cron only runs while WSL is up.

Train flags: `--device` (default `0`), `--epochs` (50), `--imgsz` (640), `--model` (`yolov8n.pt`). Requires `uv sync --extra yolo`.

## Makefile

Run from the repo root. `.PHONY` targets:

| Target | Action |
|---|---|
| `make sitl` | Build `media/smoke.mp4` if missing, then `docker compose up -d` |
| `make sitl-down` / `make down` | `docker compose down` |
| `make smoke-video` | `ffmpeg` `testsrc` → `media/smoke.mp4` (8 s, 1280×720, 15 fps) |
| `make inbox-frames` | 1 fps unlabeled stills from the backyard clip into `weeds/inbox/` |
| `make promote-inbox` | Copy boxed backyard stills into `weeds/dataset/{train,val}` |
| `make backend` | `uv run weed-spray` |
| `make vision` | `uv run weed-spray-vision` |
| `make dashboard` | `cd dashboard && npm install && npm run dev` |
| `make accept` | `uv run weed-spray-accept --out var/last-run.md` |
| `make test` | `uv run pytest -q` |
| `make lint` | `uv run ruff check src tests` |
| `make fmt` | `uv run ruff format src tests` |
| `make check` | ruff check + format `--check` + pytest |

`make sitl` starts **only** PX4 SIH, MediaMTX, and the ffmpeg publisher. Backend, vision, and dashboard stay on the host.

## Dashboard npm scripts

From `dashboard/`:

| Script | Action |
|---|---|
| `npm run dev` | Vite on `127.0.0.1:8080` (`strictPort`) |
| `npm run build` | `tsc -b && vite build` |
| `npm run preview` | Serve the production bundle on `:8080` |

Vite proxies `/api` → `http://127.0.0.1:8000` (prefix stripped) and `/ws` → `ws://127.0.0.1:8000`.
