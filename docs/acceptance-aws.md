# Acceptance testing (AWS EC2 operator host)

Remote full live SITL UAT on an **AWS EC2 operator host** so SprayPO need not use Brian’s WSL laptop. Same four-process contract and grader as [acceptance.md](acceptance.md) / [`bot_files/sitl_loop.md`](../bot_files/sitl_loop.md). **Not** live SITL on the shared Grok Bot VM (no Docker there for this loop).

Normative grader: `weed_spray.harness.accept` (`make accept` / `uv run weed-spray-accept`). FakeVehicle-only bot-vm gate: [testing.md](testing.md) (`make check`).

Host/automation scripts named below land in a **Spray Dev follow-up PR** (Refs #10). Brian owns the AWS account, budget, and launch template. This doc is the docs slice only.

## Honest scope

| Path | What runs | Who |
|---|---|---|
| **Bot VM** | `make check` / FakeVehicle only — **no** Docker / live PX4 SIH | SprayPO / Grok bots |
| **Brian WSL** | Full live SITL (`make sitl` + host apps + `make accept`) | Primary laptop path — [acceptance.md](acceptance.md) |
| **AWS EC2 operator host** | Same full live SITL stack as WSL, start/stop only | This runbook — SprayPO calls `scripts/aws_uat/*.sh`; Spray Dev owns those scripts |

## Cost cap ($10 USD / calendar month)

Hard cap for tagged weed-spray UAT resources: **$10 USD per calendar month**.

- Budget name: **`weed-spray-sitl-uat`** (AWS Budgets Cost Budget, monthly, amount **$10 USD**).
- Tag filter: `Project=weed-spray` and `Purpose=sitl-uat` (use these on every UAT resource).
- If month-to-date **actual** or **forecast** would pass **$10**, or the budget is in **ALARM**: **stop all AWS UAT** until the next calendar month begins.
- Resources **always shut down when not in use** (`scripts/aws_uat/stop_host.sh` stops the instance; never leave billable UAT idle). Always-on EC2 is forbidden.

### How SprayPO/bots detect and obey

Before every start, run **`scripts/aws_uat/budget_ok.sh`** (lands with Spray Dev). Non-zero exit is a **hard stop**: do not start EC2; wait until the next calendar month. The script must exit non-zero when month-to-date actual **or** forecast is **>= $10**, or when budget `weed-spray-sitl-uat` is in ALARM.

### AWS Budget alarm (recipe)

Brian creates once if bots cannot:

1. Tag every UAT resource (EC2, EBS, etc.) with `Project=weed-spray` and `Purpose=sitl-uat`.
2. Create Cost Budget named **`weed-spray-sitl-uat`**, filtered to those tags, monthly, **$10 USD**.
3. Alerts: e.g. actual 80% and 100%; forecasted 100%. Notify Brian (and any bot-safe SNS/email already in the account).
4. Bots use least-privilege read of budget status via `budget_ok.sh`; they never raise the cap.

## Prerequisites

Defaults (assumptions, correctable):

- Region: **`us-west-2`**
- Instance: **`t3.large`** (bump to `t3.xlarge` only if OOM)
- AMI: Ubuntu 22.04 with Docker; launch template name **`weed-spray-sitl-uat`** (Brian creates once)
- Brian owns AWS account + initial IAM + budget + launch template; bots use least privilege after

On the EC2 operator host:

- Same compose images as `compose.yaml` / [sitl.md](sitl.md). Do not pull extras at runtime.
- Repo clone of `master`; Python env with dev extras; dashboard packages if needed (same as [acceptance.md](acceptance.md)).

## Network

- **Preferred:** Tailscale on the EC2 host.
- Dashboard / API / vision bind **localhost** on the host.
- SprayPO reaches them via Tailscale IP, or an SSH local forward, for ports **8000 / 8080 / 8090**.
- Security group: **no** `0.0.0.0/0` on app ports; SSH only from a known path.
- **Never** open `:8080` / `:8000` / `:8090` to the public internet.

Brian / Spray Dev own the Tailscale/SG details; this runbook does not invent ACLs.

## Start order (on the EC2 host)

Same four processes as [acceptance.md](acceptance.md), all on the **EC2 operator host** (not the bot VM):

1. `make sitl` — builds media smoke video if missing, then brings compose up detached
2. Vision injector (`make vision`) — port 8090
3. Backend GCS (`make backend`) — port 8000
4. Dashboard (`make dashboard`) — port 8080

`scripts/aws_uat/start_host.sh` starts the tagged instance (or launch-template path), waits until SSH/Tailscale is up, pulls `master`, runs `make sitl`, and reminds the operator to start the three host apps (exact app start may be extended by Spray Dev).

## Run the grader

With all four processes up on EC2:

- Run `make accept` (same as `weed-spray-accept` writing `var/last-run.md`).
- Collect `var/last-run.md` and/or browser UAT notes as evidence before teardown.

### Expected SIH result

Identical honesty to [acceptance.md](acceptance.md). PX4 SIH has **no** `DISTANCE_SENSOR`. On the default `make sitl` path:

| | Expected |
|---|---|
| Exit code | `1` (not `0`) |
| Step 7 | `fail` — hover samples `missing` |
| Steps 8–9 | `blocked` (first fail stops the grade) |
| Step 10 | still runs if the vehicle armed |

Do not invent rangefinder PX4 params to fake a green table. Exit `0` only with rangefinder data (hardware or a Gazebo lidar profile) — **not** default compose.

## SprayPO UAT sequence (post-merge / on-demand)

1. **Budget gate** — run `scripts/aws_uat/budget_ok.sh`. Non-zero → hard stop until next calendar month.
2. **Start host** — `scripts/aws_uat/start_host.sh` (tagged EC2 / launch template `weed-spray-sitl-uat`; wait SSH/Tailscale; pull `master`; `make sitl`; remind host apps).
3. **Host apps** — vision, backend, dashboard on the EC2 host (see start order).
4. **UAT** — SprayPO browser via Tailscale or SSH forward to ports 8080 / 8000, and/or `make accept` on the host → save `var/last-run.md`.
5. **Stop** — `scripts/aws_uat/stop_host.sh` (compose down on host, then **STOP** instance — not terminate by default). Do not leave idle billable UAT running.
6. **On failure** — SprayPO opens detailed GitHub issues. SprayPO does **not** merge or implement fixes.

### Scripts (Spray Dev follow-up)

These paths are locked names; **scripts land with Spray Dev** (Refs #10). They are **not** on `master` yet:

| Script | Role |
|---|---|
| `scripts/aws_uat/budget_ok.sh` | Exit 0 only if month-to-date actual and forecast are under $10 and budget `weed-spray-sitl-uat` is not in ALARM; else exit 1 |
| `scripts/aws_uat/start_host.sh` | Start tagged EC2 (or launch template); wait SSH/Tailscale; git pull master; make sitl; remind host apps |
| `scripts/aws_uat/stop_host.sh` | Compose down on host; STOP instance (not terminate by default) |

SprayPO calls those only; no always-on. Tags on resources: `Project=weed-spray`, `Purpose=sitl-uat`.

## Do not

- Leave always-on / idle billable EC2 (or other UAT resources) running.
- Run live Docker / PX4 SIH on the shared Grok Bot VM.
- Open dashboard `:8080`, API `:8000`, or vision `:8090` to the world (`0.0.0.0/0`).
- Invent rangefinder PX4 params to force `make accept` exit `0`.
- Arm, Offboard, or pulse a pump on **real** aircraft / hardware ([SAFETY.md](../agent_prompts/_shared/SAFETY.md), [safety.md](safety.md)).
- Exceed the **$10 USD / calendar month** cap; start UAT when `budget_ok.sh` fails.
- Terminate the instance by default (stop unless Spray Dev documents otherwise).

## Related

- Laptop live SITL: [acceptance.md](acceptance.md)
- Compose / SIH: [sitl.md](sitl.md)
- FakeVehicle gate: [testing.md](testing.md)
- Contract: [`bot_files/sitl_loop.md`](../bot_files/sitl_loop.md)
- Safety: [`agent_prompts/_shared/SAFETY.md`](../agent_prompts/_shared/SAFETY.md), [safety.md](safety.md)
- Issue: [#10](https://github.com/bi21an5a1b07-bot/weed-spray/issues/10) (docs slice here; scripts/host automation remain Spray Dev)
