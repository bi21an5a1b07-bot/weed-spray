#!/usr/bin/env bash
# Launch virgin EC2 from launch template weed-spray-sitl-uat only, then
# clone → uv sync --extra dev → npm (dashboard) → make sitl.
# Contract: docs/acceptance-aws.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGION="${AWS_REGION:-us-west-2}"
LT_NAME="${AWS_UAT_LAUNCH_TEMPLATE:-weed-spray-sitl-uat}"
SSH_USER="${AWS_UAT_SSH_USER:-ubuntu}"
SSH_KEY="${AWS_UAT_SSH_KEY:-}"
STATE_DIR="${AWS_UAT_STATE_DIR:-${ROOT}/.state}"
REPO_URL="${AWS_UAT_REPO_URL:-https://github.com/bi21an5a1b07-bot/weed-spray.git}"
REPO_DIR="${AWS_UAT_REPO_DIR:-weed-spray}"

export AWS_DEFAULT_REGION="${REGION}"

bash "${ROOT}/budget_ok.sh"

mkdir -p "${STATE_DIR}"

if [[ -z "${SSH_KEY}" ]]; then
  echo "start_host: set AWS_UAT_SSH_KEY to the SSH private key path" >&2
  exit 1
fi

echo "start_host: launching from launch template '${LT_NAME}' (no resume-stopped)"
run_json="$(aws ec2 run-instances \
  --launch-template "LaunchTemplateName=${LT_NAME}" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Project,Value=weed-spray},{Key=Purpose,Value=sitl-uat}]" \
  --output json)"

INSTANCE_ID="$(RUN_JSON="${run_json}" python3 -c 'import json,os; print(json.loads(os.environ["RUN_JSON"])["Instances"][0]["InstanceId"])')"
echo "${INSTANCE_ID}" > "${STATE_DIR}/instance_id"
echo "start_host: instance ${INSTANCE_ID}"

HOST=""
for _ in $(seq 1 60); do
  desc="$(aws ec2 describe-instances --instance-ids "${INSTANCE_ID}" --output json)"
  mapfile -t _fields < <(DESC_JSON="${desc}" python3 -c 'import json,os
d=json.loads(os.environ["DESC_JSON"])
i=d["Reservations"][0]["Instances"][0]
print(i["State"]["Name"])
print(i.get("PublicIpAddress") or "")
print(i.get("PrivateIpAddress") or "")
')
  STATE="${_fields[0]}"
  PUB="${_fields[1]}"
  PRIV="${_fields[2]}"
  if [[ "${STATE}" == "running" ]]; then
    if [[ -n "${PUB}" ]]; then
      HOST="${PUB}"
    else
      HOST="${PRIV}"
    fi
    if [[ -n "${HOST}" ]]; then
      break
    fi
  fi
  sleep "${AWS_UAT_POLL_SECONDS:-5}"
done

if [[ -z "${HOST}" ]]; then
  echo "start_host: timed out waiting for instance address" >&2
  exit 1
fi
echo "${HOST}" > "${STATE_DIR}/host"
echo "start_host: host ${HOST}"

SSH=(ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -i "${SSH_KEY}" "${SSH_USER}@${HOST}")

if [[ "${AWS_UAT_SKIP_SSH_WAIT:-}" != "1" ]]; then
  for _ in $(seq 1 60); do
    if "${SSH[@]}" "true" 2>/dev/null; then
      break
    fi
    sleep "${AWS_UAT_POLL_SECONDS:-5}"
  done
  "${SSH[@]}" "true"
fi

if [[ "${AWS_UAT_DRY_BOOTSTRAP:-}" == "1" ]]; then
  "${SSH[@]}" "git clone ${REPO_URL} ${REPO_DIR} && cd ${REPO_DIR} && uv sync --extra dev && (cd dashboard && npm install) && make sitl"
else
  "${SSH[@]}" "set -euo pipefail; git clone ${REPO_URL} ${REPO_DIR}; cd ${REPO_DIR}; uv sync --extra dev; if [[ -f dashboard/package.json ]]; then (cd dashboard && npm install); fi; make sitl"
fi

cat <<MSG
start_host: SITL compose requested on ${HOST}.
remind: start host apps on the EC2 box (not the bot VM):
  1) make vision    # :8090
  2) make backend   # :8000
  3) make dashboard # :8080
default SprayPO reachability: ssh -L 8000:127.0.0.1:8000 -L 8080:127.0.0.1:8080 -L 8090:127.0.0.1:8090 ${SSH_USER}@${HOST}
MSG
