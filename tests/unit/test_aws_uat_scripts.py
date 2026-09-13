"""AWS UAT host scripts: budget gate, launch-template start, terminate teardown."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts" / "aws_uat"


def _write_exec(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _fake_bin_dir(tmp_path: Path) -> Path:
    d = tmp_path / "bin"
    d.mkdir()
    return d


def _run_script(
    name: str,
    *,
    env: dict[str, str],
    path_prefix: Path,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    script = SCRIPTS / name
    assert script.is_file(), f"missing {script}"
    full_env = os.environ.copy()
    full_env.update(env)
    full_env["PATH"] = f"{path_prefix}:{full_env.get('PATH', '')}"
    return subprocess.run(
        ["bash", str(script)],
        cwd=cwd or REPO,
        env=full_env,
        text=True,
        capture_output=True,
        check=False,
    )


def _install_aws_stub(bin_dir: Path, log: Path, behavior: str) -> None:
    """behavior: ok_under | actual_ge | forecast_ge | alarm | missing_budget | launch | stop"""
    # Built without an f-string so JSON braces stay literal; only log/behavior substituted.
    body = r"""#!/usr/bin/env bash
set -euo pipefail
echo "$@" >> "LOG_PATH"
cmd="$1"; shift || true
case "$cmd" in
  budgets)
    sub="$1"; shift || true
    case "$sub" in
      describe-budget)
        case "BEHAVIOR" in
          missing_budget)
            echo "Budget not found" >&2
            exit 254
            ;;
          actual_ge)
            cat <<'JSON'
{"Budget":{"BudgetName":"weed-spray-sitl-uat","BudgetLimit":{"Amount":"10","Unit":"USD"},"CalculatedSpend":{"ActualSpend":{"Amount":"10.00","Unit":"USD"},"ForecastedSpend":{"Amount":"8.00","Unit":"USD"}}}}
JSON
            ;;
          forecast_ge)
            cat <<'JSON'
{"Budget":{"BudgetName":"weed-spray-sitl-uat","BudgetLimit":{"Amount":"10","Unit":"USD"},"CalculatedSpend":{"ActualSpend":{"Amount":"3.00","Unit":"USD"},"ForecastedSpend":{"Amount":"12.50","Unit":"USD"}}}}
JSON
            ;;
          *)
            cat <<'JSON'
{"Budget":{"BudgetName":"weed-spray-sitl-uat","BudgetLimit":{"Amount":"10","Unit":"USD"},"CalculatedSpend":{"ActualSpend":{"Amount":"2.00","Unit":"USD"},"ForecastedSpend":{"Amount":"4.00","Unit":"USD"}}}}
JSON
            ;;
        esac
        ;;
      *)
        echo "unexpected budgets $sub" >&2
        exit 2
        ;;
    esac
    ;;
  cloudwatch)
    sub="$1"; shift || true
    if [[ "$sub" == "describe-alarms" ]]; then
      if [[ "BEHAVIOR" == "alarm" ]]; then
        cat <<'JSON'
{"MetricAlarms":[{"AlarmName":"weed-spray-sitl-uat","StateValue":"ALARM"}]}
JSON
      else
        echo '{"MetricAlarms":[]}'
      fi
    else
      echo "unexpected cloudwatch $sub" >&2
      exit 2
    fi
    ;;
  sts)
    echo '{"Account":"123456789012"}'
    ;;
  ec2)
    sub="$1"; shift || true
    case "$sub" in
      run-instances)
        echo '{"Instances":[{"InstanceId":"i-testuat001","PrivateIpAddress":"10.0.0.9"}]}'
        ;;
      start-instances)
        echo "start-instances must not be used" >&2
        exit 99
        ;;
      describe-instances)
        if [[ "$*" == *"--output text"* ]]; then
          if [[ "$*" == *"--filters"* && "$*" != *"--instance-ids"* ]]; then
            printf '%s	%s
' "i-testuat001" "i-testuat002"
          else
            echo "i-testuat001"
          fi
        elif [[ "$*" == *"--filters"* && "$*" != *"--instance-ids"* ]]; then
          cat <<'JSON'
{"Reservations":[{"Instances":[{"InstanceId":"i-testuat001","State":{"Name":"running"}},{"InstanceId":"i-testuat002","State":{"Name":"stopped"}}]}]}
JSON
        else
          cat <<'JSON'
{"Reservations":[{"Instances":[{"InstanceId":"i-testuat001","State":{"Name":"running"},"PublicIpAddress":"203.0.113.9","PrivateIpAddress":"10.0.0.9"}]}]}
JSON
        fi
        ;;
      terminate-instances)
        echo '{"TerminatingInstances":[{"InstanceId":"ok"}]}'
        ;;
      stop-instances)
        echo "stop-instances must not be default teardown" >&2
        exit 99
        ;;
      describe-volumes)
        if [[ "$*" == *"--output text"* ]]; then
          echo "vol-orphanuat"
        else
          echo '{"Volumes":[{"VolumeId":"vol-orphanuat"}]}'
        fi
        ;;
      delete-volume)
        echo "deleted $*"
        ;;
      describe-addresses)
        echo '{"Addresses":[]}'
        ;;
      describe-nat-gateways)
        echo '{"NatGateways":[]}'
        ;;
      wait)
        exit 0
        ;;
      *)
        echo "unexpected ec2 $sub" >&2
        exit 2
        ;;
    esac
    ;;
  *)
    echo "unexpected aws $cmd" >&2
    exit 2
    ;;
esac
"""
    body = body.replace("LOG_PATH", str(log)).replace("BEHAVIOR", behavior)
    _write_exec(bin_dir / "aws", body)


def _install_ssh_stub(bin_dir: Path, log: Path) -> None:
    body = f"""#!/usr/bin/env bash
set -euo pipefail
echo "ssh $*" >> "{log}"
remote_cmd="${{@: -1}}"
if [[ "$remote_cmd" == *"git clone"* ]] || [[ "$*" == *"git clone"* ]]; then
  echo "cloned"
  exit 0
fi
if [[ "$*" == *"uv sync"* ]]; then
  echo "synced"
  exit 0
fi
if [[ "$*" == *"npm"* ]]; then
  echo "npm ok"
  exit 0
fi
if [[ "$*" == *"make sitl"* ]]; then
  echo "sitl up"
  exit 0
fi
if [[ "$*" == *"compose down"* ]] || [[ "$*" == *"docker compose down"* ]]; then
  echo "compose down"
  exit 0
fi
exit 0
"""
    _write_exec(bin_dir / "ssh", body)


@pytest.fixture
def bin_dir(tmp_path: Path) -> Path:
    return _fake_bin_dir(tmp_path)


def test_budget_ok_passes_under_cap(bin_dir: Path, tmp_path: Path):
    log = tmp_path / "aws.log"
    _install_aws_stub(bin_dir, log, "ok_under")
    r = _run_script(
        "budget_ok.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_BUDGET_NAME": "weed-spray-sitl-uat",
            "AWS_UAT_COST_CAP": "10",
            "AWS_ACCOUNT_ID": "123456789012",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode == 0, r.stderr


def test_budget_ok_fails_when_actual_ge_cap(bin_dir: Path, tmp_path: Path):
    log = tmp_path / "aws.log"
    _install_aws_stub(bin_dir, log, "actual_ge")
    r = _run_script(
        "budget_ok.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_BUDGET_NAME": "weed-spray-sitl-uat",
            "AWS_UAT_COST_CAP": "10",
            "AWS_ACCOUNT_ID": "123456789012",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode == 1, r.stdout + r.stderr


def test_budget_ok_fails_when_forecast_ge_cap(bin_dir: Path, tmp_path: Path):
    log = tmp_path / "aws.log"
    _install_aws_stub(bin_dir, log, "forecast_ge")
    r = _run_script(
        "budget_ok.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_BUDGET_NAME": "weed-spray-sitl-uat",
            "AWS_UAT_COST_CAP": "10",
            "AWS_ACCOUNT_ID": "123456789012",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode == 1


def test_budget_ok_fails_when_alarm(bin_dir: Path, tmp_path: Path):
    log = tmp_path / "aws.log"
    _install_aws_stub(bin_dir, log, "alarm")
    r = _run_script(
        "budget_ok.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_BUDGET_NAME": "weed-spray-sitl-uat",
            "AWS_UAT_COST_CAP": "10",
            "AWS_ACCOUNT_ID": "123456789012",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode == 1


def test_budget_ok_uses_us_east_1_for_budgets_and_alarms(bin_dir: Path, tmp_path: Path):
    """AWS Budgets (+ billing alarms) are us-east-1-only; EC2 default stays us-west-2."""
    log = tmp_path / "aws.log"
    _install_aws_stub(bin_dir, log, "ok_under")
    r = _run_script(
        "budget_ok.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_BUDGET_NAME": "weed-spray-sitl-uat",
            "AWS_UAT_COST_CAP": "10",
            "AWS_ACCOUNT_ID": "123456789012",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode == 0, r.stderr
    lines = log.read_text().strip().splitlines()
    budget_lines = [ln for ln in lines if ln.startswith("budgets ")]
    cw_lines = [ln for ln in lines if ln.startswith("cloudwatch ")]
    assert budget_lines, lines
    assert cw_lines, lines
    for ln in budget_lines + cw_lines:
        assert "--region us-east-1" in ln, ln
    assert not any(ln.startswith("ec2 ") for ln in lines)


def test_start_host_refuses_when_budget_fails(bin_dir: Path, tmp_path: Path):
    log = tmp_path / "aws.log"
    _install_aws_stub(bin_dir, log, "actual_ge")
    _install_ssh_stub(bin_dir, tmp_path / "ssh.log")
    r = _run_script(
        "start_host.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_BUDGET_NAME": "weed-spray-sitl-uat",
            "AWS_UAT_COST_CAP": "10",
            "AWS_UAT_LAUNCH_TEMPLATE": "weed-spray-sitl-uat",
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_UAT_SSH_USER": "ubuntu",
            "AWS_UAT_SSH_KEY": str(tmp_path / "id"),
            "AWS_UAT_DRY_BOOTSTRAP": "1",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode != 0
    assert "run-instances" not in log.read_text() if log.exists() else True


def test_start_host_launches_from_template_not_resume(bin_dir: Path, tmp_path: Path):
    log = tmp_path / "aws.log"
    ssh_log = tmp_path / "ssh.log"
    _install_aws_stub(bin_dir, log, "launch")
    _install_ssh_stub(bin_dir, ssh_log)
    (tmp_path / "id").write_text("fake-key\n")
    r = _run_script(
        "start_host.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_BUDGET_NAME": "weed-spray-sitl-uat",
            "AWS_UAT_COST_CAP": "10",
            "AWS_UAT_LAUNCH_TEMPLATE": "weed-spray-sitl-uat",
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_UAT_SSH_USER": "ubuntu",
            "AWS_UAT_SSH_KEY": str(tmp_path / "id"),
            "AWS_UAT_STATE_DIR": str(tmp_path / "state"),
            "AWS_UAT_DRY_BOOTSTRAP": "1",
            "AWS_UAT_SKIP_SSH_WAIT": "1",
            "AWS_UAT_POLL_SECONDS": "0",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    aws_log = log.read_text()
    assert "run-instances" in aws_log
    assert (
        "launch-template" in aws_log
        or "LaunchTemplate" in aws_log
        or "weed-spray-sitl-uat" in aws_log
    )
    assert "start-instances" not in aws_log


def test_stop_host_terminates_not_stop_only(bin_dir: Path, tmp_path: Path):
    log = tmp_path / "aws.log"
    ssh_log = tmp_path / "ssh.log"
    _install_aws_stub(bin_dir, log, "stop")
    _install_ssh_stub(bin_dir, ssh_log)
    state = tmp_path / "state"
    state.mkdir()
    (state / "instance_id").write_text("i-testuat001\n")
    (state / "host").write_text("203.0.113.9\n")
    r = _run_script(
        "stop_host.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_STATE_DIR": str(state),
            "AWS_UAT_SSH_USER": "ubuntu",
            "AWS_UAT_SSH_KEY": str(tmp_path / "id"),
            "AWS_UAT_PROJECT_TAG": "weed-spray",
            "AWS_UAT_PURPOSE_TAG": "sitl-uat",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    aws_log = log.read_text()
    assert "terminate-instances" in aws_log
    assert "stop-instances" not in aws_log
    assert "delete-volume" in aws_log


def test_stop_host_terminates_all_tagged_instances(bin_dir: Path, tmp_path: Path):
    """Teardown must not leave a second tagged UAT EC2 billing (BugScout #13)."""
    log = tmp_path / "aws.log"
    ssh_log = tmp_path / "ssh.log"
    _install_aws_stub(bin_dir, log, "stop")
    _install_ssh_stub(bin_dir, ssh_log)
    state = tmp_path / "state"
    state.mkdir()
    (state / "instance_id").write_text("i-testuat001\n")
    (state / "host").write_text("203.0.113.9\n")
    r = _run_script(
        "stop_host.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_STATE_DIR": str(state),
            "AWS_UAT_SSH_USER": "ubuntu",
            "AWS_UAT_SSH_KEY": str(tmp_path / "id"),
            "AWS_UAT_PROJECT_TAG": "weed-spray",
            "AWS_UAT_PURPOSE_TAG": "sitl-uat",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    aws_log = log.read_text()
    term_lines = [ln for ln in aws_log.splitlines() if "terminate-instances" in ln]
    assert term_lines, aws_log
    joined = " ".join(term_lines)
    assert "i-testuat001" in joined
    assert "i-testuat002" in joined


def test_start_host_terminates_on_fail_after_launch(bin_dir: Path, tmp_path: Path):
    """After run-instances, any failure must terminate — no orphan UAT bill."""
    log = tmp_path / "aws.log"
    _install_aws_stub(bin_dir, log, "launch")
    # SSH always fails (bootstrap / connectivity)
    _write_exec(
        bin_dir / "ssh",
        """#!/usr/bin/env bash
set -euo pipefail
echo "ssh fail $*" >&2
exit 1
""",
    )
    (tmp_path / "id").write_text("fake-key\n")
    r = _run_script(
        "start_host.sh",
        env={
            "AWS_REGION": "us-west-2",
            "AWS_UAT_BUDGET_NAME": "weed-spray-sitl-uat",
            "AWS_UAT_COST_CAP": "10",
            "AWS_UAT_LAUNCH_TEMPLATE": "weed-spray-sitl-uat",
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_UAT_SSH_USER": "ubuntu",
            "AWS_UAT_SSH_KEY": str(tmp_path / "id"),
            "AWS_UAT_STATE_DIR": str(tmp_path / "state"),
            "AWS_UAT_DRY_BOOTSTRAP": "1",
            "AWS_UAT_SKIP_SSH_WAIT": "1",
            "AWS_UAT_POLL_SECONDS": "0",
        },
        path_prefix=bin_dir,
    )
    assert r.returncode != 0
    aws_log = log.read_text()
    assert "run-instances" in aws_log
    assert "terminate-instances" in aws_log
    assert "i-testuat001" in aws_log
