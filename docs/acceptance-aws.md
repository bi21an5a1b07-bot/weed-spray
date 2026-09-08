# Acceptance testing (AWS EC2 operator host)

Remote full live SITL UAT on an **AWS EC2 operator host** so SprayPO need not use Brian’s WSL laptop. Same four-process contract and grader as [acceptance.md](acceptance.md) / [`bot_files/sitl_loop.md`](../bot_files/sitl_loop.md). **Not** live SITL on the shared Grok Bot VM (no Docker there for this loop).

Normative grader: `weed_spray.harness.accept` (`make accept` / `uv run weed-spray-accept`). FakeVehicle-only bot-vm gate: [testing.md](testing.md) (`make check`).

Host/automation scripts named below land in a **Spray Dev follow-up PR** (Refs #10). Brian owns the AWS account, budget, and launch template. This doc is the docs slice only.

## Honest scope

| Path | What runs | Who |
|---|---|---|
| **Bot VM** | `make check` / FakeVehicle only — **no** Docker / live PX4 SIH | SprayPO / Grok bots |
| **Brian WSL** | Full live SITL (`make sitl` + host apps + `make accept`) | Primary laptop path — [acceptance.md](acceptance.md) |
| **AWS EC2 operator host** | Same full live SITL stack as WSL, launch-template start + full teardown | This runbook — SprayPO calls `scripts/aws_uat/*.sh`; Spray Dev owns those scripts |

## Cost cap ($10 USD / calendar month)

Hard cap for tagged weed-spray UAT resources: **$10 USD per calendar month**.

- Budget name: **`weed-spray-sitl-uat`** (AWS Budgets Cost Budget, monthly, amount **$10 USD**).
- Tag filter: `Project=weed-spray` and `Purpose=sitl-uat` (use these on every UAT resource).
- If month-to-date **actual** or **forecast** is **>= $10**, or the budget is in **ALARM**: **stop all AWS UAT** until the next calendar month begins.
- **Every AWS resource that costs money** and is tagged for this UAT (`Project=weed-spray`, `Purpose=sitl-uat`) is **torn down when not in use** — not only “stop the EC2.” That includes EC2 **and** any EBS volumes, Elastic IPs, NAT gateways, load balancers, or other billable attachments created for UAT.
- **Default teardown = terminate/delete** (locked option **(a)**): after each UAT, `scripts/aws_uat/stop_host.sh` **terminates** the instance and **deletes** attached/orphan UAT volumes and other tagged billable resources so ongoing UAT charges are **zero**. A stopped instance that still bills root EBS is **not** the default path.
- Start only via launch template **`weed-spray-sitl-uat`** (no “resume a stopped instance” default).
- Dormant paid spend = **none** unless Brian explicitly accepts it in writing later. Always-on / idle UAT spend is forbidden.

### How SprayPO/bots detect and obey

Before every start, run **`scripts/aws_uat/budget_ok.sh`** (lands with Spray Dev). Non-zero exit is a **hard stop**: do not start EC2; wait until the next calendar month. The script must exit non-zero when month-to-date actual **or** forecast is **>= $10**, or when budget `weed-spray-sitl-uat` is in ALARM.

## Human AWS setup (Brian / operator, once)

One-time human setup **before** bots run UAT. Bots do **not** create the AWS account, place Marketplace orders, or raise the spend cap. After this checklist is done, configure the **AWS Grok Bot plugin** so SprayPO / scripts can call AWS for start/teardown UAT (credentials stay in the plugin / IAM — never paste long-lived keys into chat or `/workspace`).

### 1. Account

1. Use (or create) an AWS account Brian controls for weed-spray UAT.
2. Prefer a dedicated account or a clearly isolated OU/project so UAT spend is easy to see against the **$10/mo** cap.
3. Enable billing alerts / Cost Explorer access for the operator identity.

### 2. Region and tags

1. Default region: **`us-west-2`**.
2. Agree the tag pair on **every** UAT resource: `Project=weed-spray`, `Purpose=sitl-uat`.
3. Enforce tags on create where possible (org tag policy or launch-template tag specs) so Budgets and `stop_host.sh` can find orphans.

### 3. Cost Budget

1. Create AWS Budgets **Cost Budget** named **`weed-spray-sitl-uat`**.
2. Period: **monthly**; amount: **$10 USD**.
3. Filter: resources tagged `Project=weed-spray` **and** `Purpose=sitl-uat`.
4. Alerts: e.g. actual **80%** and **100%**; forecasted **100%**. Notify Brian (email / SNS already in the account).
5. `budget_ok.sh` later reads this budget; hard stop when actual or forecast is **>= $10**, or budget is in **ALARM**.

### 4. Launch template

1. Create launch template name **`weed-spray-sitl-uat`**.
2. AMI: Ubuntu **22.04** with **Docker** installed (and compose-capable tooling).
3. Instance type default: **`t3.large`** (bump to `t3.xlarge` only if OOM on first real run).
4. Tag instance + volumes with `Project=weed-spray`, `Purpose=sitl-uat`.
5. AMI ships **Docker and base tools only** (compose-capable). It does **not** pre-bake the weed-spray repo or Python/npm env. Repo bootstrap on a virgin LT box is **`scripts/aws_uat/start_host.sh`'s job** (exact bake of Docker/base tools is Spray Dew’s follow-up).
6. **No always-on** instance — template only; each UAT **launches** then **terminates/deletes**.

### 5. Network and SSH key

1. Create (or reuse) an SSH key pair the operator and bots’ automation can use; store the private key only in the agreed secret store / plugin — **never** in the repo or chat.
2. Security group: allow **SSH** only from a known path (operator IP, bastion, or bot egress you control). **No** `0.0.0.0/0` on app ports **8000 / 8080 / 8090**.
3. Default SprayPO reachability after setup: **ssh `-L`** for those ports (apps may bind localhost).

### 6. IAM (least privilege for bots / plugin)

1. Create an IAM principal (user or role) for the **AWS Grok Bot plugin** / `scripts/aws_uat/*.sh`.
2. Allow only what UAT needs, for example: describe/list budgets; run-instances from launch template `weed-spray-sitl-uat`; terminate instances; delete tagged UAT volumes/EIPs; describe instances/tags in `us-west-2`. Deny broad admin.
3. Wire that principal into the AWS Grok Bot plugin **after** steps 1–5. Do not paste access keys into chat, issues, or `/workspace`.

### 7. Done when

- [ ] Budget `weed-spray-sitl-uat` exists at **$10/mo** with tag filter + alerts
- [ ] Launch template `weed-spray-sitl-uat` launches a Docker-capable Ubuntu host in `us-west-2`
- [ ] SSH key + locked-down SG in place
- [ ] Least-privilege IAM ready
- [ ] AWS Grok Bot plugin configured to that account/role
- [ ] A dry `budget_ok.sh` → `start_host.sh` → teardown `stop_host.sh` leaves **zero** ongoing tagged UAT charges

## Prerequisites (each UAT run)

Defaults (from human setup above):

- Region **`us-west-2`**, launch template **`weed-spray-sitl-uat`**, instance **`t3.large`**
- Budget gate + terminate/delete teardown (see Cost cap)

On the EC2 operator host after launch (done by `start_host.sh` on a **virgin** LT box — not a `git pull`-only path):

- Same compose images as `compose.yaml` / [sitl.md](sitl.md). Do not pull extras at runtime.
- `git clone` of `bi21an5a1b07-bot/weed-spray` (track `master`); then `uv sync --extra dev`; then `npm` install in `dashboard/` if needed (same as [acceptance.md](acceptance.md)); then `make sitl` + host-app remind.

## Network

- Dashboard / API / vision **may bind localhost** (`127.0.0.1`) on the EC2 host.
- **Default path for SprayPO:** SSH local forward — `ssh -L` for ports **8000 / 8080 / 8090** (works with localhost bind).
- **Tailscale** is optional and only valid if apps **also listen on the Tailscale interface** (not localhost-only). Do not claim Tailscale IP reachability while apps stay on `127.0.0.1` alone.
- Security group: **no** `0.0.0.0/0` on app ports; SSH only from a known path.
- **Never** open `:8080` / `:8000` / `:8090` to the public internet.

Brian / Spray Dev own SSH keys and any optional Tailscale/SG details; this runbook does not invent ACLs.

## Start order (on the EC2 host)

Same four processes as [acceptance.md](acceptance.md), all on the **EC2 operator host** (not the bot VM):

1. `make sitl` — builds media smoke video if missing, then brings compose up detached
2. Vision injector (`make vision`) — port 8090
3. Backend GCS (`make backend`) — port 8000
4. Dashboard (`make dashboard`) — port 8080

`scripts/aws_uat/start_host.sh` **launches a new instance from launch template `weed-spray-sitl-uat` only** (not resume-stopped), waits until SSH is up, then on the **virgin** box: `git clone` `bi21an5a1b07-bot/weed-spray` → `uv sync --extra dev` (and `npm` in `dashboard/` if needed) → `make sitl`, and reminds the operator to start the three host apps (exact app start may be extended by Spray Dev). **No `git pull`-only path** — AMI has Docker/base tools only; full repo bootstrap is this script's job.

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
2. **Start host** — `scripts/aws_uat/start_host.sh` (**launch template `weed-spray-sitl-uat` only**; wait SSH; on virgin box: `git clone` → `uv sync --extra dev` (+ npm in `dashboard/` if needed) → `make sitl`; remind host apps). **No `git pull`-only path.**
3. **Host apps** — vision, backend, dashboard on the EC2 host (see start order); bind may be localhost.
4. **UAT** — SprayPO reaches ports via **ssh `-L` for 8000/8080/8090** by default (Tailscale only if apps listen on the Tailscale iface), and/or `make accept` on the host → save `var/last-run.md`.
5. **Teardown all costed UAT** — `scripts/aws_uat/stop_host.sh` (compose down; **terminate** instance; **delete** tagged EBS/EIP/NAT/etc. if present). Outcome: **zero ongoing UAT charges** by default. Do not leave any costed UAT resource billing idle.
6. **On failure** — SprayPO opens detailed GitHub issues. SprayPO does **not** merge or implement fixes.

### Scripts (Spray Dev follow-up)

These paths are locked names; **scripts land with Spray Dev** (Refs #10). They are **not** on `master` yet:

| Script | Role |
|---|---|
| `scripts/aws_uat/budget_ok.sh` | Exit 0 only if month-to-date actual **and** forecast are **< $10** and budget `weed-spray-sitl-uat` is not in ALARM; else exit 1 (hard stop at **>= $10** actual or forecast, or ALARM) |
| `scripts/aws_uat/start_host.sh` | Launch **only** from template `weed-spray-sitl-uat` (no resume-stopped default); wait SSH; on virgin LT box: `git clone` bi21an5a1b07-bot/weed-spray → `uv sync --extra dev` (+ npm in `dashboard/` if needed) → `make sitl`; remind host apps. AMI = Docker/base tools only; **no `git pull`-only path** |
| `scripts/aws_uat/stop_host.sh` | Compose down; **terminate** instance; **delete** tagged costed UAT resources (EBS/EIP/NAT/etc. if present) so ongoing UAT charges are **zero** by default. Stopped-but-EBS-billing is not the default. Dormant spend only if Brian accepts in writing later (default none). |

SprayPO calls those only; no always-on. Tags on resources: `Project=weed-spray`, `Purpose=sitl-uat`.

## Do not

- Leave **any** costed tagged UAT resource running or billing idle (EC2, EBS, EIP, NAT, or other) when UAT is not in use.
- Use “stop instance, keep root EBS” as the default teardown (that still bills).
- Resume a stopped UAT instance as the default start path (start via launch template only).
- Use a **`git pull`-only** path on the operator host (virgin LT box must `git clone` + `uv sync --extra dev` + `make sitl`; AMI does not ship the repo).
- Claim Tailscale IP reachability while apps bind **localhost only** (use ssh `-L`, or bind apps on the Tailscale iface too).
- Run live Docker / PX4 SIH on the shared Grok Bot VM.
- Open dashboard `:8080`, API `:8000`, or vision `:8090` to the world (`0.0.0.0/0`).
- Invent rangefinder PX4 params to force `make accept` exit `0`.
- Arm, Offboard, or pulse a pump on **real** aircraft / hardware ([SAFETY.md](../agent_prompts/_shared/SAFETY.md), [safety.md](safety.md)).
- Exceed the **$10 USD / calendar month** cap; start UAT when `budget_ok.sh` fails.
- Invent a dormant paid exception; only Brian may accept one explicitly (default: none).

## Related

- Laptop live SITL: [acceptance.md](acceptance.md)
- Compose / SIH: [sitl.md](sitl.md)
- FakeVehicle gate: [testing.md](testing.md)
- Contract: [`bot_files/sitl_loop.md`](../bot_files/sitl_loop.md)
- Safety: [`agent_prompts/_shared/SAFETY.md`](../agent_prompts/_shared/SAFETY.md), [safety.md](safety.md)
- Issue: [#10](https://github.com/bi21an5a1b07-bot/weed-spray/issues/10) (docs slice here; scripts/host automation remain Spray Dev)
