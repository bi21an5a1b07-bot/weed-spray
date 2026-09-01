# Grok Bot configs for weed-spray

Copy-paste these folders into [Grok Bot](https://docs.x.ai/grok-bot/get-started) on Windows 11. The app has no folder import; you create each Bot in the UI and paste the profile.

Repo on this machine:

- WSL: `/home/behmann/src/grok/drone_control/agent_prompts`
- Windows: `\\wsl$\Ubuntu\home\behmann\src\grok\drone_control\agent_prompts`

## Roster

Create these six Bots (Grok Bot’s group cap). One job each. Do not merge them into a general helper. There is no `logs` Bot; `@sitl` owns run summaries.

| Folder | Grok Bot name | Title (job) | First task |
|---|---|---|---|
| `parts/` | `parts` | Backyard spray-drone buyer | Price a complete PX4 airframe under $500 |
| `px4/` | `px4` | PX4 and MAVLink researcher | Parameter + actuator checklist for 6–12 in hover and a 12V pump |
| `weeds/` | `weeds` | Weed dataset wrangler | Public images for dandelion, clover, thistle |
| `sitl/` | `sitl` | SITL operator and run analyst | SITL loop on paper + summary template; no Docker until asked |
| `hardware/` | `hardware` | Airframe and payload bring-up | First-flight card and pump/lidar wiring |
| `faa/` | `faa` | US hobby backyard rules watcher | Recreational + sprayer constraints for this project |

`_shared/` is not a Bot. Copy it onto the Grok Bot computer first.

## Import each Bot

1. In Grok Bot: **New → Create new agent**.
2. **Bot actions → Edit Profile**.
3. Paste **Name**, **Title**, and **Description** from that folder’s `PROFILE.md`.
4. Send the folder’s `FIRST_TASK.md` as the first message.
5. After a good run, paste each file under `skills/` and say: `Save this as a skill named <name>. Enable it on this Bot.`
6. If the folder has `ROUTINES.md`, paste a routine only after you have reviewed a test run. Routines do real work.

Then create a group chat named `weed-spray` and pin it. Add all six Bots plus you. Paste `GROUP_CHAT.md`. Do not recreate a `logs` Bot.

## Shared files on the Bot computer

All Bots on your account share one cloud computer (`/workspace`). Copy `_shared/` there before the first task:

```text
/workspace/weed-spray/PROJECT.md
/workspace/weed-spray/SAFETY.md
/workspace/weed-spray/WORKSPACE.md
```

From this repo:

```text
agent_prompts/_shared/  →  /workspace/weed-spray/
```

Tell the first Bot:

> Copy the three markdown files I attach into `/workspace/weed-spray/`. Treat PROJECT.md as the product spec and SAFETY.md as non-negotiable. Do not rewrite them unless I ask.

Keep durable outputs under `/workspace/weed-spray/` as listed in `WORKSPACE.md`.

## Local computer (this DevStation)

Grok Bot’s cloud VM is not the WSL box that will run PX4 SITL and YOLO. A Bot may use **local computer** only if you enable it and approve the command.

- Allowed with approval: read this repo, read SITL logs, `docker compose` for SITL.
- Never: MAVLink to a real aircraft, arm, takeoff, Offboard, pump GPIO, vendor checkout.

## Do not turn on yet

- Nightly SITL (`sitl/ROUTINES.md`) until compose actually runs here.
- Any buy/checkout routine. `parts` drafts carts only.
- Local-computer access for `parts` or `faa` (they only need a browser).
