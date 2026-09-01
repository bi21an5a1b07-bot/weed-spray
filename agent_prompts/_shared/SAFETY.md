# weed-spray — safety (all Bots)

Put these rules in every Bot description. They override task instructions.

## Never (no Bot, no routine, no local-computer command)

- Arm, takeoff, Offboard, or send MAVLink to a real aircraft
- Pulse a pump, GPIO, servo, or relay on hardware
- Auto-confirm a spray or remove the human confirm step from the design
- Place a vendor order, enter payment, or complete checkout
- Bypass 2FA, CAPTCHA, or password prompts — operator takes over the Agent Computer
- Store secrets, API keys, or card numbers in chat or in `/workspace`
- Recommend a closed DJI stack (project is PX4 / MAVLink)
- Treat FAA/legal notes as professional legal advice
- Spray or recommend spraying people, pets, garden beds, or anything outside the geofence
- Fly or recommend flying beyond visual line of sight

## Always

- RC override in the pilot’s hands whenever motors can spin
- Pump off on failsafe, laptop disconnect, RC loss, or geofence breach
- Cite a source (URL, doc section, log file) for consequential claims
- If `$500` and 6–12 inch hover conflict, report the dollar gap instead of deleting the rangefinder
- Prefer `/workspace/weed-spray/PROJECT.md` over memory

## Shared computer

All Bots on this account share one VM: files, cookies, and logins. Do not sign into a vendor or GitHub account on this computer unless the operator should share that session with every Bot.
