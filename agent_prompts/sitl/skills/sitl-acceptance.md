Save this as a skill named **sitl-acceptance**. Enable it on the `sitl` Bot.

When to use: operator asks if SITL is ready, how to run it, or to grade a log from a run.

Inputs: PROJECT.md, sitl/loop.md, optional uploaded logs.

Steps (cloud-only by default):

1. Read loop.md. If missing, write it first.
2. If the operator uploaded logs, fill sitl/last-run.md with pass/fail per step and write sitl/summaries/YYYY-MM-DD-HHMM-<sitl|hw>.md from _template.md. Copy real numbers only. Extra pump pulses are defects.
3. If they ask you to run Docker: refuse unless local-computer is enabled **and** they approve in this turn. Then only the compose file in the weed-spray repo, no extra images.
4. Never open UDP to anything except localhost SITL. Never fetch logs from a vehicle.

Validate: pump-off-on-failsafe is a required step. Hover altitude is recorded or marked missing.

Approval: any local command. Ask before deleting logs.
