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

## Live accept (needs SITL)

All of: `make sitl`, vision, backend, dashboard, then:

```bash
uv run weed-spray-accept --out var/last-run.md
```

Grades `bot_files/sitl_loop.md`. SIH hover step is expected to fail without a rangefinder.

## What is not tested here

- Browser E2E (Playwright)
- Real Kakute / USB CDC
- Ultralytics training (dataset empty by design)
