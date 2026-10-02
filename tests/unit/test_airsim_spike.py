"""Issue #66 AirSim spike contracts. No live Unreal, PX4, or Docker."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_airsim_spike_doc_locks_topology_and_recommendation():
    """Spike doc keeps SIH/Gazebo default and refuses AirSim NAV_RCL_ACT=0."""
    text = (REPO / "docs/sitl-airsim.md").read_text()
    assert "issue #66" in text
    assert "Windows host" in text
    assert "WSL2" in text
    assert "v1.12.3" in text
    assert "px4io/px4-sitl:latest" in text
    assert "NAV_RCL_ACT" in text
    assert "get_images" in text
    assert "PixelStreaming" in text
    assert "Runtime" in text
    assert "8554/cam" in text
    assert "make sitl-gz" in text
    assert "Keep SIH" in text
    assert "not a replacement" in text.lower() or "does not replace" in text.lower()


def test_airsim_does_not_replace_gazebo_compose():
    """Accurate SITL stays compose.gazebo.yaml. No AirSim compose yet."""
    gz = (REPO / "compose.gazebo.yaml").read_text()
    assert "px4io/px4-sitl-gazebo" in gz
    assert "PX4_SIM_MODEL: gz_x500_lidar_down" in gz
    makefile = (REPO / "Makefile").read_text()
    assert "sitl-gz:" in makefile
    assert not (REPO / "compose.airsim.yaml").exists()


def test_sitl_and_readme_point_at_the_spike():
    sitl = (REPO / "docs/sitl.md").read_text()
    readme = (REPO / "docs/README.md").read_text()
    assert "sitl-airsim.md" in sitl
    assert "sitl-airsim.md" in readme
    grok = (REPO / "GROK.md").read_text()
    assert "AirSim" in grok
