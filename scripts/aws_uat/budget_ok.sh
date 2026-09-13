#!/usr/bin/env bash
# Exit 0 only if weed-spray SITL UAT budget actual AND forecast are < cap
# and no matching CloudWatch alarm is in ALARM. Else exit 1 (hard stop).
# Contract: docs/acceptance-aws.md
#
# EC2 UAT stays in AWS_REGION (default us-west-2). AWS Budgets and billing
# CloudWatch alarms are us-east-1-only — always call those with --region us-east-1.
set -euo pipefail

REGION="${AWS_REGION:-us-west-2}"
BILLING_REGION="${AWS_UAT_BILLING_REGION:-us-east-1}"
BUDGET_NAME="${AWS_UAT_BUDGET_NAME:-weed-spray-sitl-uat}"
COST_CAP="${AWS_UAT_COST_CAP:-10}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"

# Keep default region on the EC2 UAT region (do not point it at billing).
export AWS_DEFAULT_REGION="${REGION}"

if [[ -z "${ACCOUNT_ID}" ]]; then
  ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
fi

if ! budget_json="$(aws budgets describe-budget \
  --region "${BILLING_REGION}" \
  --account-id "${ACCOUNT_ID}" \
  --budget-name "${BUDGET_NAME}" \
  --output json 2>/dev/null)"; then
  echo "budget_ok: cannot describe budget '${BUDGET_NAME}' in ${BILLING_REGION} (fail closed)" >&2
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
  --region "${BILLING_REGION}" \
  --alarm-name-prefix "${BUDGET_NAME}" \
  --state-value ALARM \
  --output json)"

ALARM_COUNT="$(ALARM_JSON="${alarms_json}" python3 -c 'import json,os; print(len(json.loads(os.environ["ALARM_JSON"]).get("MetricAlarms") or []))')"
if [[ "${ALARM_COUNT}" != "0" ]]; then
  echo "budget_ok: ${ALARM_COUNT} CloudWatch alarm(s) in ALARM for prefix '${BUDGET_NAME}' (${BILLING_REGION})" >&2
  exit 1
fi

echo "budget_ok: alarms=0 billing_region=${BILLING_REGION} ec2_region=${REGION}"
exit 0
