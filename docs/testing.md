# Testing

Python changes are not done until Ruff and pytest both pass. Config: `[tool.ruff]` in `pyproject.toml` ([Ruff](https://docs.astral.sh/ruff/)).

## Ruff (lint + format)

```bash
uv sync --extra dev
uv run ruff check src tests          # lint
uv run ruff format src tests         # write
uv run ruff format --check src tests # CI-style: fail if unformatted
make lint                            # ruff check
make fmt                             # ruff format
make check                           # lint + format --check + pytest
```

`make test` is pytest only. `make check` is the full Python gate.

## Unit + integration (no PX4)

```bash
uv sync --extra dev
uv run pytest -q
```

Uses `tests/fakes.py` (`FakeVehicle`) so MAVSDK never starts. Each test module has a docstring listing its scope; function names are the assertions. Coverage:

- Geo, class map, distance parsing, Pydantic models
- Mission: inject/confirm/reject, RC vs dashboard takeoff, unconfirmed never sprayed, kill/people, failsafe idle skip
- Vision HTTP: class rejection, inject overwrite
- Backend HTTP on the same asyncio loop as mission tasks
- Compose/port contracts, dashboard route strings, harness last-run table
- hover AGL: `WEED_HOVER_ALTITUDE_MODE=offboard_agl` uses FakeVehicle `goto_global_agl` (no live PX4)
- extract_clip dry-run: hermetic tmp media (no gitignored backyard clip)
- aws_uat scripts: budget_ok / start_host / stop_host with PATH stubs (no live AWS)
- compose.gazebo.yaml: opt-in gz_x500_lidar_down pin + Makefile sitl-gz (no live Docker)

## Live accept (needs SITL)

Full operator runbook: [acceptance.md](acceptance.md).

All of: `make sitl`, vision, backend, dashboard, then:

```bash
make accept
# same as: uv run weed-spray-accept --out var/last-run.md
```

Grades `bot_files/sitl_loop.md`. SIH hover step is expected to fail without a rangefinder. Gazebo (`make sitl-gz` + `make backend-gz`) is the path that can pass step 7.

`make accept` does not start a detector. Vision modes, the overlay, georeference, and the train gate have their own checks in [acceptance.md](acceptance.md#vision-and-georeference).

## What is not tested here

- Browser E2E (Playwright). The overlay click is a manual check.
- Real Kakute / USB CDC
- A full Ultralytics training run (the empty-class and orphan-label gates are unit-tested; training itself is operator-run)
