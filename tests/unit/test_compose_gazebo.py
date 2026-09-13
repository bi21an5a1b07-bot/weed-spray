"""Opt-in Gazebo compose contract (issue #19) — no live Docker / no PyYAML."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_compose_gazebo_exists_and_pins_lidar_down():
    path = REPO / "compose.gazebo.yaml"
    text = path.read_text()
    assert "px4io/px4-sitl-gazebo" in text
    assert "PX4_SIM_MODEL: gz_x500_lidar_down" in text
    assert 'HEADLESS: "1"' in text or "HEADLESS: '1'" in text or "HEADLESS: 1" in text
    assert "network_mode: host" in text
    assert "host.docker.internal:127.0.0.1" in text
    assert "rtsp-pub" not in text  # no file RTSP publisher on gz profile
    assert "/media/smoke" not in text


def test_makefile_has_sitl_gz_targets():
    text = (REPO / "Makefile").read_text()
    assert "sitl-gz:" in text
    assert "sitl-gz-down:" in text
    assert "compose.gazebo.yaml" in text
    assert "sitl: smoke-video" in text
    # down tears both profiles
    assert "down: sitl-down sitl-gz-down" in text


def test_makefile_start_targets_tear_other_profile_first():
    """Both profiles use host networking — starting one must down the other (BugScout #21)."""
    text = (REPO / "Makefile").read_text()
    idx_gz = text.index("sitl-gz:")
    idx_gz_down = text.index("sitl-gz-down:")
    body_gz = text[idx_gz:idx_gz_down]
    assert "sitl-down" in body_gz
    assert "compose.gazebo.yaml up" in body_gz

    idx_sitl = text.index("sitl: smoke-video")
    idx_sitl_down = text.index("sitl-down:")
    body_sitl = text[idx_sitl:idx_sitl_down]
    assert "sitl-gz-down" in body_sitl
    assert "docker compose up" in body_sitl
