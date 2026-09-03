#!/bin/bash
# Local bot_files hash check. No LLM, no network.
# Exit 0 always so cron does not mail. Delta is var/bot_files-pending.
set -u
ROOT=/home/behmann/src/grok/drone_control
PY="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/scripts/bot_files_delta.py"
LOG="$ROOT/var/bot_files-cron.log"
LAST="$ROOT/var/bot_files-last.json"
FLAG="$ROOT/var/bot_files-pending"
mkdir -p "$ROOT/var"
cd "$ROOT" || exit 0
ts=$(date -Iseconds)
if [ ! -x "$PY" ]; then
  echo "$ts missing venv python $PY" >>"$LOG"
  exit 0
fi
out=$("$PY" "$SCRIPT" 2>&1) || code=$?
code=${code:-0}
printf '%s\n' "$out" >"$LAST"
if [ "$code" -eq 0 ]; then
  echo "$ts unchanged" >>"$LOG"
  rm -f "$FLAG"
else
  echo "$ts DELTA" >>"$LOG"
  printf '%s\n' "$out" >>"$LOG"
  printf '%s\n' "$out" >"$FLAG"
fi
if [ -f "$LOG" ]; then
  tail -n 400 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
exit 0
