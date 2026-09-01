# Group chat: `weed-spray`

Grok Bot allows **six Bots per group**. This roster is exactly six. There is no `logs` Bot; `@sitl` owns run summaries.

**Members:** you, `parts`, `px4`, `weeds`, `sitl`, `hardware`, `faa`

Paste this as the first group message:

---

This channel is the weed-spray program.

Shared spec: `/workspace/weed-spray/PROJECT.md`
Safety: `/workspace/weed-spray/SAFETY.md`
File layout: `/workspace/weed-spray/WORKSPACE.md`

Rules for every Bot in this chat:

- One job. If work belongs to another Bot, write the file and @ them instead of doing it.
- `@sitl` owns SITL loop docs **and** after-action summaries (`sitl/last-run.md` and `sitl/summaries/`). There is no `logs` Bot.
- No MAVLink to hardware. No pump. No checkout. No auto-spray.
- Cite sources. Put durable output under `/workspace/weed-spray/`.

First pass (do not wait on each other more than one file):

1. `@parts` — live BOM vs $500, including lidar + flow + ELRS
2. `@px4` — hover + pump + Offboard checklist
3. `@weeds` — public datasets for dandelion, clover, thistle (no big downloads)
4. `@sitl` — acceptance loop on paper (no Docker) plus `/workspace/weed-spray/sitl/summaries/_template.md` (detections, confirms, hover 6–12 in, pump pulse, failsafe, geofence)
5. `@hardware` — wiring + first-flight card from the BOM (or marked assumptions)
6. `@faa` — recreational + vinegar snapshot, not legal advice

I am the only one who confirms sprays, arms, or spends money. Ping me if blocked.
---
