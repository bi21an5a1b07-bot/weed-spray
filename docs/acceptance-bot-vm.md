# Acceptance on the bot computer (no live SITL)

How Grok Bot / shared-box agents run an **honest** acceptance bar on **this computer** (the bot VM). This is **in addition to** the operator WSL live loop in [acceptance.md](acceptance.md).

Do **not** run `make sitl` or `make accept` here and call it acceptance. Those need Brian's WSL Docker host (UDP 14540 to SIH, MediaMTX, host ffmpeg). Clarify bot-VM vs operator-WSL before promising a live loop.

## What this path is

| | Bot computer | Operator WSL |
|---|---|---|
| Where | Shared Grok Bot Linux box | DevStation / WSL |
| Green bar | `make check` (ruff + pytest) | Live 10-step `make accept` |
| Vehicle | `tests/fakes.py` `FakeVehicle` — no MAVSDK, no PX4 | Real SIH over MAVSDK `:14540` |
| Contract still true | Human confirm, no invented PX4 params, class map | Same + `bot_files/sitl_loop.md` rows |

## Prerequisites

Checkout of `bi21an5a1b07-bot/weed-spray` on the bot computer. Python tooling via [mise](https://mise.jdx.dev/walkthrough.html) or `uv` on PATH:

```bash
mise trust && mise install
uv sync --extra dev
```

Docker / PX4 / MediaMTX are **not** required for this path.

## Run the bar

```bash
make check
# same gates: ruff check + ruff format --check + pytest -q
```

Or stepwise:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest -q
```

Exit `0` means lint/format clean and the FakeVehicle suite passed. That is the green bar for the bot computer.

## What pytest covers (no PX4)

From [testing.md](testing.md) / `tests/`:

- Geo, class map, models (incl. `"class"` alias)
- Mission: inject / confirm / reject, RC vs dashboard takeoff, unconfirmed never sprayed, kill / people hold
- Vision HTTP: unknown class rejection, inject overwrite
- Backend HTTP ASGI + `FakeVehicle` (connect / fence / inject / confirm / visit / kill)
- Compose/port contract strings, harness last-run table shape
- `extract_clip` hermetic dry-run (tmp media; no gitignored backyard clip)

## What this path does **not** prove

- Live MAVSDK HEARTBEAT / Offboard on UDP 14540
- RTSP / MediaMTX / dashboard process-up
- The 10-step `weed-spray-accept` table (`var/last-run.md`)
- SIH hover AGL / `DISTANCE_SENSOR` (step 7)
- Real Kakute / USB CDC / pump GPIO

For those, use [acceptance.md](acceptance.md) on **operator WSL**, or paste `var/last-run.md` from that host for review.

## Do not

- Start Docker SIH on the bot VM and treat a failed `make accept` as a docs/setup mystery — the live loop is not supported here.
- Invent PX4 params or drop rangefinder/flow requirements to fake a green live table.
- Auto-confirm sprays or skip human-confirm semantics in tests (suite already asserts inject is not confirm).
- Claim bot-VM `make check` replaces operator `make accept`.

## Related

- Live SITL runbook: [acceptance.md](acceptance.md)
- Pytest / ruff details: [testing.md](testing.md)
- CLI: [cli.md](cli.md) (`make check`, `make test`)
- Contract for the live loop: [`bot_files/sitl_loop.md`](../bot_files/sitl_loop.md)
