#!/usr/bin/env bash
# Exit 0 only if weed-spray SITL UAT budget actual AND forecast are < cap
# and no matching CloudWatch alarm is in ALARM. Else exit 1 (hard stop).
# Contract: docs/acceptance-aws.md
set -euo pipefail

REGION="${AWS_REGION:-us-west-2}"
BUDGET_NAME="${AWS_UAT_BUDGET_NAME:-weed-spray-sitl-uat}"
COST_CAP="${AWS_UAT_COST_CAP:-10}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"

export AWS_DEFAULT_REGION="${REGION}"

if [[ -z "${ACCOUNT_ID}" ]]; then
  ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
fi

if ! budget_json="$(aws budgets describe-budget \
  --account-id "${ACCOUNT_ID}" \
  --budget-name "${BUDGET_NAME}" \
  --output json 2>/dev/null)"; then
  echo "budget_ok: cannot describe budget '${BUDGET_NAME}' (fail closed)" >&2
  exit 1
fi

BUDGET_JSON="${budget_json}" COST_CAP="${COST_CAP}" python3 - <<'PY'
import json, os, sys

cap = float(os.environ["COST_CAP"])
try:
    data = json.loads(os.environ["BUDGET_JSON"])
    spend = data["Budget"]["CalculatedSpend"]
    actual = float(spend["ActualSpend"]["Amount"])
    forecast = float(spend.get("ForecastedSpend", {}).get("Amount") or 0)
except Exception as e:
    print(f"budget_ok: parse error: {e}", file=sys.stderr)
    sys.exit(1)

if actual >= cap:
    print(f"budget_ok: actual {actual} >= cap {cap}", file=sys.stderr)
    sys.exit(1)
if forecast >= cap:
    print(f"budget_ok: forecast {forecast} >= cap {cap}", file=sys.stderr)
    sys.exit(1)

print(f"budget_ok: actual={actual} forecast={forecast} cap={cap}", flush=True)
PY

alarms_json="$(aws cloudwatch describe-alarms \
  --alarm-name-prefix "${BUDGET_NAME}" \
  --state-value ALARM \
  --output json)"

ALARM_COUNT="$(ALARM_JSON="${alarms_json}" python3 -c 'import json,os; print(len(json.loads(os.environ["ALARM_JSON"]).get("MetricAlarms") or []))')"
if [[ "${ALARM_COUNT}" != "0" ]]; then
  echo "budget_ok: ${ALARM_COUNT} CloudWatch alarm(s) in ALARM for prefix '${BUDGET_NAME}'" >&2
  exit 1
fi

echo "budget_ok: alarms=0"
exit 0
