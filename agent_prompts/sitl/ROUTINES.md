# Routines for `sitl`

Do not enable until Grok Build has a compose file and one manual pass.

## Nightly SITL (local computer — off by default)

Only after a manual run is green:

> Every weekday at 07:00 in my local timezone, on the DevStation with local-computer approval already granted, run the weed-spray SITL acceptance from sitl/loop.md.
> Write `/workspace/weed-spray/sitl/last-run.md`.
> Post pass/fail and the first failing step.
> If Docker is not running or compose is missing, report failure; do not install software.
> Never connect to USB, serial, or a real vehicle.

Until then, keep this routine paused.
