"""loop.md pass/fail script. First fail stops the grade; remaining rows = blocked.
Pump-off-on-kill still runs if the vehicle was armed.
"""

from __future__ import annotations

import argparse
import socket
import sys
import time
from pathlib import Path

import httpx

BACKEND = "http://127.0.0.1:8000"
VISION = "http://127.0.0.1:8090"
RTSP_HOST, RTSP_PORT = "127.0.0.1", 8554
STEPS = [
    "1 connect",
    "2 typed geofence box",
    "3 scan",
    "4 inject or detect boxes",
    "5 confirm subset",
    "6 visit",
    "7 6-12 in hover",
    "8 0.75 s pump pulse",
    "9 RTL",
    "10 pump-off on kill",
]


def rtsp_open() -> bool:
    """True if MediaMTX answers RTSP OPTIONS on ``8554/cam``."""
    try:
        with socket.create_connection((RTSP_HOST, RTSP_PORT), timeout=2.0) as sock:
            sock.sendall(b"OPTIONS rtsp://127.0.0.1:8554/cam RTSP/1.0\r\nCSeq: 1\r\n\r\n")
            data = sock.recv(256)
            return data.startswith(b"RTSP/") or b"200" in data or b"401" in data
    except OSError:
        return False


def write_last_run(path: Path, results: dict[str, tuple[str, str]]) -> None:
    """Write the 10-step markdown table. Missing steps become ``blocked``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# sitl last-run",
        "",
        "| Step | Result | Notes |",
        "|---|---|---|",
    ]
    for step in STEPS:
        result, notes = results.get(step, ("blocked", "not reached"))
        lines.append(f"| {step} | {result} | {notes} |")
    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Drive the live loop.md sequence. Return 1 if any step failed."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="var/last-run.md")
    args = parser.parse_args(argv)
    results: dict[str, tuple[str, str]] = {}
    failed = False
    armed = False
    st: dict = {}

    def grade(step: str, ok: bool, notes: str) -> None:
        """Record pass/fail. After the first fail, further grades are blocked."""
        nonlocal failed
        if failed:
            results[step] = ("blocked", notes)
            return
        if ok:
            results[step] = ("pass", notes)
        else:
            results[step] = ("fail", notes)
            failed = True

    with httpx.Client(timeout=30.0) as http:
        rtsp = rtsp_open()
        dash_ok = False
        try:
            dash_ok = http.get("http://127.0.0.1:8080", timeout=2.0).status_code < 500
        except httpx.HTTPError:
            pass
        vision_ok = False
        try:
            vision_ok = http.get(f"{VISION}/health").json().get("ok") is True
        except httpx.HTTPError:
            pass
        connected = False
        try:
            body = http.post(f"{BACKEND}/connect", timeout=60.0).json()
            connected = body.get("phase") == "connected" or body.get("telemetry", {}).get(
                "connected"
            )
        except httpx.HTTPError as exc:
            grade(STEPS[0], False, f"backend connect: {exc}")
        else:
            grade(
                STEPS[0],
                bool(connected and rtsp and dash_ok and vision_ok),
                f"mav={connected} rtsp={rtsp} dash={dash_ok} injector={vision_ok}",
            )

        try:
            http.post(
                f"{BACKEND}/fence",
                json={"north_m": 20, "south_m": -5, "east_m": 15, "west_m": -15},
            ).raise_for_status()
            grade(STEPS[1], True, "box N20 S-5 E15 W-15")
        except httpx.HTTPError as exc:
            grade(STEPS[1], False, str(exc))

        payload = {
            "detections": [
                {"id": "w1", "class": "dandelion", "north_m": 6.0, "east_m": 4.0},
                {"id": "w2", "class": "clover", "north_m": 8.0, "east_m": -3.0},
                {"id": "w3", "class": "thistle", "north_m": 3.0, "east_m": 2.0},
            ]
        }
        try:
            http.post(f"{BACKEND}/detections/inject", json=payload).raise_for_status()
            grade(STEPS[3], True, "injected w1 dandelion, w2 clover, w3 thistle")
        except httpx.HTTPError as exc:
            grade(STEPS[3], False, str(exc))

        try:
            http.post(f"{BACKEND}/scan", json={"source": "dashboard"}).raise_for_status()
            armed = True
            deadline = time.time() + 180
            phase = ""
            while time.time() < deadline:
                phase = http.get(f"{BACKEND}/state").json()["phase"]
                if phase in {"awaiting_confirm", "killed", "error"}:
                    break
                time.sleep(1)
            grade(STEPS[2], phase == "awaiting_confirm", f"phase={phase}")
        except httpx.HTTPError as exc:
            grade(STEPS[2], False, str(exc))

        try:
            http.post(f"{BACKEND}/confirm", json={"ids": ["w1"]}).raise_for_status()
            st = http.get(f"{BACKEND}/state").json()
            confirmed = [
                c["detection_id"] for c in st.get("confirms", []) if c.get("decision") == "confirm"
            ]
            if not confirmed:
                confirmed = [d["id"] for d in st["detections"] if d.get("confirmed")]
            grade(STEPS[4], confirmed == ["w1"], f"confirmed={confirmed}")
        except httpx.HTTPError as ext:
            grade(STEPS[4], False, str(ext))

        try:
            http.post(f"{BACKEND}/visit").raise_for_status()
            deadline = time.time() + 180
            while time.time() < deadline:
                st = http.get(f"{BACKEND}/state").json()
                if st["phase"] in {"rtl", "killed", "error"}:
                    break
                time.sleep(1)
            visited = [d["id"] for d in st.get("detections", []) if d.get("visited")]
            grade(STEPS[5], "w1" in visited and "w2" not in visited, f"visited={visited}")
        except httpx.HTTPError as exc:
            grade(STEPS[5], False, str(exc))

        hover = st.get("hover_agl_m") or []
        has_missing = False
        numeric: list[float] = []
        for x in hover:
            if isinstance(x, dict):
                if x.get("missing") or x.get("agl_m") == "missing":
                    has_missing = True
                elif isinstance(x.get("agl_m"), (int, float)):
                    numeric.append(float(x["agl_m"]))
            elif x == "missing":
                has_missing = True
            elif isinstance(x, (int, float)):
                numeric.append(float(x))
        in_band = bool(numeric) and all(0.15 <= v <= 0.30 for v in numeric)
        grade(
            STEPS[6],
            bool(in_band) and not has_missing,
            f"hover_agl_m={hover} (SIH distance_sensor expected missing)",
        )

        pulses = st.get("pump_pulses") or []
        durations = [p.get("duration_s") for p in pulses]
        extra = len(pulses) != 1
        ok_dur = bool(durations) and all(
            abs(float(d) - 0.75) < 0.2 for d in durations if d is not None
        )
        grade(
            STEPS[7],
            (not extra) and ok_dur,
            f"pulses={len(pulses)} durations={durations}",
        )

        grade(STEPS[8], st.get("phase") in {"rtl", "killed"}, f"phase={st.get('phase')}")

        try:
            killed = http.post(f"{BACKEND}/kill").json()
            events = killed.get("pump_off_events") or []
            off = any(e.get("pump_commanded_off") for e in events) or (
                killed.get("telemetry", {}).get("pump_value") == 0
            )
            if not armed and failed:
                results[STEPS[9]] = ("blocked", "vehicle never armed")
            else:
                results[STEPS[9]] = ("pass" if off else "fail", f"events={len(events)}")
                if not off:
                    failed = True
        except httpx.HTTPError as exc:
            results[STEPS[9]] = ("fail", str(exc))
            failed = True

    out = Path(args.out)
    write_last_run(out, results)
    print(out.read_text())
    return 1 if any(v[0] == "fail" for v in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
