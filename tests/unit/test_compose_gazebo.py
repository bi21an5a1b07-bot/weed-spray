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
    assert "rtsp-pub" not in text
    assert "/media/smoke" not in text
    assert "cam-bridge" not in text  # MediaMTX ingests RTP directly
    assert "mediamtx-gazebo.yml" in text


def test_compose_projects_are_isolated():
    """Distinct compose project names so down of one cannot remove the other (BugScout)."""
    sih = (REPO / "compose.yaml").read_text()
    gz = (REPO / "compose.gazebo.yaml").read_text()
    assert "name: weed-spray-sih" in sih
    assert "name: weed-spray-gz" in gz
    assert "name: weed-spray-sih" not in gz
    assert "name: weed-spray-gz" not in sih


def test_lidar_cam_overlay_model_present():
    model = REPO / "sitl/gz/models/x500_lidar_down/model.sdf"
    text = model.read_text()
    assert "gpu_lidar" in text
    assert "mono_cam" in text
    assert "CameraJoint" in text


def test_mediamtx_gazebo_ingests_rtp_with_sdp():
    """GstCameraSystem H264 PT 96 needs udp+rtp + rtpSDP (BugScout #23)."""
    text = (REPO / "sitl/mediamtx-gazebo.yml").read_text()
    assert "udp+rtp://127.0.0.1:5600" in text
    assert "rtpSDP:" in text
    assert "payload" not in text.lower() or "96" in text
    assert "a=rtpmap:96 H264/90000" in text
    assert "source: publisher" not in text  # SIH file publisher is separate yml


def test_makefile_has_sitl_gz_targets():
    text = (REPO / "Makefile").read_text()
    assert "sitl-gz:" in text
    assert "sitl-gz-down:" in text
    assert "compose.gazebo.yaml" in text
    assert "sitl: smoke-video" in text
    assert "down: sitl-down sitl-gz-down" in text


def test_makefile_start_targets_tear_other_profile_first():
    """Both profiles use host networking — starting one must down the other (BugScout #21)."""
    text = (REPO / "Makefile").read_text()
    idx_gz = text.index("sitl-gz:")
    idx_gz_down = text.index("sitl-gz-down:")
    body_gz = text[idx_gz:idx_gz_down]
    assert "sitl-down" in body_gz
    assert "compose.gazebo.yaml" in body_gz and "up" in body_gz
    assert "weed-spray-gz" in body_gz

    idx_sitl = text.index("sitl: smoke-video")
    idx_sitl_down = text.index("sitl-down:")
    body_sitl = text[idx_sitl:idx_sitl_down]
    assert "sitl-gz-down" in body_sitl
    assert "weed-spray-sih" in body_sitl and "up" in body_sitl
