# weed-spray documentation

Laptop ground station for a backyard PX4 quad that finds dandelion, clover, and thistle and, after a human confirm, hovers 6–12 inches AGL and pulses a 12 V household vinegar/salt pump.

Normative product rules live in `agent_prompts/_shared/` and Grok Bot contracts in `bot_files/`. Grok Build session rules: [`GROK.md`](../GROK.md). This folder explains how the **code** implements those rules.

| Doc | Contents |
|---|---|
| [Getting started](getting-started.md) | Install, SITL up, dashboard, tests |
| [Architecture](architecture.md) | Processes, ports, mission sequence |
| [HTTP API](api.md) | Backend `:8000` and vision `:8090` |
| [SITL](sitl.md) | Docker SIH, RTSP, accept script |
| [Vision](vision.md) | Frozen classes, injector, training |
| [Hardware](hardware.md) | Kakute / Pi / pump mapping |
| [Safety](safety.md) | Confirm, RC, failsafes, FAA notes |
| [Testing](testing.md) | Ruff, pytest, live `weed-spray-accept` |
| [Code reference](code-reference.md) | Every module and function |
| [CLI and Makefile](cli.md) | `uv run` entries and `make` targets |
| [Dashboard](dashboard.md) | Vite UI on `:8080` |
| [Repository layout](repository-layout.md) | Tree of the git repo |
| [Environment](environment.md) | `WEED_*` settings |

Repo root: `/home/behmann/src/grok/drone_control`.
