#!/usr/bin/env bash
# Compose down, terminate instance, delete tagged costed UAT leftovers.
# Default teardown = terminate/delete (not stop-keep-EBS).
# Contract: docs/acceptance-aws.md
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGION="${AWS_REGION:-us-west-2}"
STATE_DIR="${AWS_UAT_STATE_DIR:-${ROOT}/.state}"
SSH_USER="${AWS_UAT_SSH_USER:-ubuntu}"
SSH_KEY="${AWS_UAT_SSH_KEY:-}"
PROJECT_TAG="${AWS_UAT_PROJECT_TAG:-weed-spray}"
PURPOSE_TAG="${AWS_UAT_PURPOSE_TAG:-sitl-uat}"

export AWS_DEFAULT_REGION="${REGION}"

INSTANCE_ID=""
HOST=""
if [[ -f "${STATE_DIR}/instance_id" ]]; then
  INSTANCE_ID="$(tr -d '[:space:]' < "${STATE_DIR}/instance_id")"
fi
if [[ -f "${STATE_DIR}/host" ]]; then
  HOST="$(tr -d '[:space:]' < "${STATE_DIR}/host")"
fi

if [[ -n "${HOST}" && -n "${SSH_KEY}" ]]; then
  ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=10 -i "${SSH_KEY}" "${SSH_USER}@${HOST}" \
    "cd weed-spray 2>/dev/null && docker compose down || true" || true
fi

if [[ -z "${INSTANCE_ID}" ]]; then
  INSTANCE_ID="$(aws ec2 describe-instances \
    --filters "Name=tag:Project,Values=${PROJECT_TAG}" \
              "Name=tag:Purpose,Values=${PURPOSE_TAG}" \
              "Name=instance-state-name,Values=pending,running,stopping,stopped" \
    --query 'Reservations[].Instances[].InstanceId' \
    --output text | awk '{print $1}')"
fi

if [[ -n "${INSTANCE_ID}" && "${INSTANCE_ID}" != "None" ]]; then
  echo "stop_host: terminate-instances ${INSTANCE_ID}"
  aws ec2 terminate-instances --instance-ids "${INSTANCE_ID}" >/dev/null
  aws ec2 wait instance-terminated --instance-ids "${INSTANCE_ID}" 2>/dev/null || true
else
  echo "stop_host: no instance id found (continuing to sweep tagged volumes)" >&2
fi

vol_ids="$(aws ec2 describe-volumes \
  --filters "Name=tag:Project,Values=${PROJECT_TAG}" \
            "Name=tag:Purpose,Values=${PURPOSE_TAG}" \
            "Name=status,Values=available" \
  --query 'Volumes[].VolumeId' --output text)"
for vol in ${vol_ids}; do
  if [[ -n "${vol}" && "${vol}" != "None" ]]; then
    echo "stop_host: delete-volume ${vol}"
    aws ec2 delete-volume --volume-id "${vol}" || true
  fi
done

addr_json="$(aws ec2 describe-addresses \
  --filters "Name=tag:Project,Values=${PROJECT_TAG}" \
            "Name=tag:Purpose,Values=${PURPOSE_TAG}" \
  --output json)"
ADDR_JSON="${addr_json}" python3 -c '
import json, os, subprocess
data = json.loads(os.environ["ADDR_JSON"])
for a in data.get("Addresses") or []:
    alloc = a.get("AllocationId")
    if alloc:
        print(f"stop_host: release-address {alloc}", flush=True)
        subprocess.run(["aws", "ec2", "release-address", "--allocation-id", alloc], check=False)
'

nat_json="$(aws ec2 describe-nat-gateways \
  --filter "Name=tag:Project,Values=${PROJECT_TAG}" \
           "Name=tag:Purpose,Values=${PURPOSE_TAG}" \
           "Name=state,Values=available,pending" \
  --output json 2>/dev/null || echo "{\"NatGateways\":[]}")"
NAT_JSON="${nat_json}" python3 -c '
import json, os, subprocess
data = json.loads(os.environ["NAT_JSON"])
for n in data.get("NatGateways") or []:
    nid = n.get("NatGatewayId")
    if nid:
        print(f"stop_host: delete-nat-gateway {nid}", flush=True)
        subprocess.run(["aws", "ec2", "delete-nat-gateway", "--nat-gateway-id", nid], check=False)
'

rm -f "${STATE_DIR}/instance_id" "${STATE_DIR}/host" 2>/dev/null || true
echo "stop_host: teardown complete (terminate/delete default; zero idle UAT charges target)"
