# Stand up weed-spray on the bot computer (SprayPO UAT)

How to install and UAT **weed-spray / SprayPO** on the **bot computer** (shared Grok Bot Linux VM). This path is for agents and bot hosts that have uv and ffmpeg but **no Docker**.

This is **not** the live SITL acceptance loop. Live accept runs on **operator WSL** (Brian) per [acceptance.md](acceptance.md). Do not treat a bot-VM install as a live SIH run. Hard refuse live `make sitl` / `make accept` on this VM.

## Honest scope

| Capability | Bot computer | Operator WSL (DevStation) |
|---|---|---|
| Where | Shared Grok Bot Linux box | Brian WSL / Docker host |
| Install | gh clone + uv sync --extra dev (+ optional dashboard pkg) | Same + container host + ffmpeg for SIH stack |
| Green UAT bar | **`make check` exit `0`** (ruff + pytest / FakeVehicle) | Live loop per [acceptance.md](acceptance.md) |
| `make sitl` / `make accept` | **Cannot / hard refuse** — no Docker | **Yes** — UDP 14540 SIH, MediaMTX, host processes |
| Default SIH accept | N/A | Expect exit 1 (step 7 fail / DISTANCE_SENSOR missing); exit 0 only with rangefinder |
| Vehicle under test | tests/fakes.py FakeVehicle - no MAVSDK, no PX4 | Real SIH over MAVSDK :14540 |

**Bot-VM UAT = clone → `uv sync` → `make check` exit `0` ONLY.** That is the SprayPO stand-up proof for this host. It does **not** replace operator `make accept`. Live UAT stays on Brian WSL; paste `var/last-run.md` for review. Do not claim live SITL works on the bot box.

## Prerequisites (this VM)

Evidence on a typical bot box:

- uv on PATH
- ffmpeg on PATH (optional for smoke video; not required for make check)
- **No Docker** then make sitl / make accept are unsupported here; hard refuse

You need a checkout of bi21an5a1b07-bot/weed-spray and network for uv sync.

## Stand-up steps

### 1. Clone

```bash
gh repo clone bi21an5a1b07-bot/weed-spray
cd weed-spray
```

(Or git clone with the same remote if gh is unavailable.)

### 2. Python deps

```bash
uv sync --extra dev
```

If mise is present:

```bash
mise trust && mise install
uv sync --extra dev
```

### 3. Optional dashboard (UI only)

Not required for make check. Useful if you want the Vite UI on :8080 while poking HTTP APIs against a FakeVehicle-backed backend later:

```bash
(cd dashboard && npm install)
# later: (cd dashboard && npm run dev) or make dashboard
```

### 4. UAT bar — `make check`

```bash
make check
```

Same gates stepwise:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest -q
```

**Pass:** exit code `0` — lint/format clean and the FakeVehicle suite passed. That is SprayPO UAT on the bot computer.

## What pytest proves

From [testing.md](testing.md) / tests/ (no PX4, no Docker):

- Geo, class map, models (incl. class alias)
- Mission: inject / confirm / reject, RC vs dashboard takeoff, unconfirmed never sprayed, kill / people hold
- Vision HTTP: unknown class rejection, inject overwrite
- Backend HTTP ASGI + FakeVehicle (connect / fence / inject / confirm / visit / kill)
- Compose/port contract strings, harness last-run table shape
- extract_clip hermetic dry-run (tmp media; no gitignored backyard clip)

Human-confirm semantics stay enforced: inject is not confirm; unconfirmed weeds are never sprayed in the suite.

## What this path does **not** prove

- Live MAVSDK HEARTBEAT / Offboard on UDP 14540
- RTSP / MediaMTX / dashboard process-up as part of weed-spray-accept
- The 10-step accept table (var/last-run.md)
- SIH hover AGL / DISTANCE_SENSOR (accept step 7)
- Real Kakute / USB CDC / pump GPIO
- That `make check` is equivalent to `make accept` — **it is not**
- Live SITL on the bot computer — **it does not work here**

## Optional: host processes without SIH

You may start vision / backend / dashboard on the bot host for manual HTTP exploration:

```bash
uv run weed-spray-vision   # :8090
uv run weed-spray          # :8000  (no real vehicle without SIH)
(cd dashboard && npm run dev)  # :8080
```

This is **not** live accept. Without Docker SIH there is no PX4 on :14540, no MediaMTX RTSP, and the accept harness is not a valid green bar here. Hard refuse live `make sitl` / `make accept` on the bot VM.

## Live SITL evidence (operator WSL only)

For the 10-step loop, use [acceptance.md](acceptance.md) on **Brian WSL**:

1. Start SIH stack + vision / backend / dashboard on the host (per acceptance.md)
2. Run the accept harness then it writes `var/last-run.md`
3. Default SIH: expect exit 1 (step 7 fail); exit 0 only with rangefinder

To review live evidence from the bot side, paste or attach `var/last-run.md` from that WSL run. Do not invent a green live table on this VM. Do not claim live SITL works on the bot box.

## Do not

- Run `make sitl` / `make accept` on the bot VM and treat failure as a docs or setup mystery; Docker SIH is not supported here; hard refuse.
- Invent PX4 params or drop rangefinder / flow requirements to fake a green live table.
- Auto-confirm sprays or skip human-confirm semantics in tests (suite already asserts inject is not confirm).
- Claim bot-VM `make check` replaces operator `make accept`.
- Claim live SITL works on this box.

## Related

- Live SITL runbook: [acceptance.md](acceptance.md)
- Pytest / ruff details: [testing.md](testing.md)
- CLI: [cli.md](cli.md) (make check, make test)
- Getting started (operator-oriented): [getting-started.md](getting-started.md)
- Contract for the live loop: [bot_files/sitl_loop.md](../bot_files/sitl_loop.md)
