"""Repo contracts: compose ports, dashboard safety strings, bot_files present."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_compose_matches_loop_ports():
    text = (ROOT / "compose.yaml").read_text()
    assert "px4io/px4-sitl" in text
    assert "sihsim_quadx" in text
    assert "8554" in text
    assert "network_mode: host" in text
    assert "rtsp://127.0.0.1:8554/cam" in text


def test_sitl_template_copied():
    path = ROOT / "sitl" / "summaries" / "_template.md"
    assert path.is_file()
    text = path.read_text()
    assert "hover_agl_m" in text
    assert "pump_off_events" in text
    assert "dandelion" in text


def test_dashboard_exposes_safety_controls():
    app = (ROOT / "dashboard" / "src" / "App.tsx").read_text()
    for needle in (
        "/connect",
        "/kill",
        "/hold-people",
        "/preflight",
        "/confirm",
        "dashboard-first",
        "RC-first",
    ):
        assert needle in app


def test_bot_files_present():
    names = {
        "weeds_class-map.md",
        "weeds_sources.md",
        "px4_actuators.md",
        "px4_offboard.md",
        "sitl_template.md",
        "faa_current.md",
        "parts_cap.md",
    }
    have = {p.name for p in (ROOT / "bot_files").iterdir()}
    assert names <= have
