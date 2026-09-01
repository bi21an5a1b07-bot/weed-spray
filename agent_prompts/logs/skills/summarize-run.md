Save this as a skill named **summarize-run**. Enable it on the `logs` Bot.

When to use: operator uploads a SITL run, ulog, or dashboard export, or asks “how did that flight go?”

Inputs: files in `/workspace/weed-spray/logs/` or attachments; `_template.md`.

Steps:

1. Identify sitl vs hardware from filenames.
2. Fill a new summary from the template. Copy real numbers only.
3. Hover: report min/max/mean AGL vs 6–12 in target. If no distance sensor field, say so.
4. Compare detection count, confirm count, pump-pulse count. Any extra pulse is a defect.
5. List failsafe and geofence events. Note whether pump commanded off.
6. End with at most five defects, severity ordered.

Validate: no invented telemetry. Extra pump pulses called out.

Approval: none for read-only summaries. Ask before deleting or fetching from a vehicle.
