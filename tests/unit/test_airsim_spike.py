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
    assert "px4io/px4-sitl-gazebo" in text
    assert "get_images" in text
    assert "PixelStreaming" in text
    assert "Runtime" in text
    assert "8554/cam" in text
    assert "make sitl-gz" in text
    assert "Keep SIH" in text
    assert "not a replacement" in text.lower() or "does not replace" in text.lower()


def test_airsim_px4_proof_requires_source_built_none_not_docker():
    """AirSim TCP 4560 needs source-built none_*; px4io Docker images will not attach."""
    text = (REPO / "docs/sitl-airsim.md").read_text()
    assert "4560" in text
    assert "none_*" in text
    assert "source-built" in text
    assert "will not" in text and "attach" in text
    # Must not claim Docker/px4io images are a valid AirSim PX4 proof path.
    assert "or the existing `px4io` images" not in text
    assert "or the existing px4io images" not in text.lower()
    # Gazebo image is not SIH's px4-sitl.
    assert "not the SIH" in text or "not the SIH `px4-sitl`" in text


def test_airsim_doc_refuses_nav_rcl_act_zero():
    """Repo must refuse copying AirSim sample NAV_RCL_ACT: 0 into our stack."""
    text = (REPO / "docs/sitl-airsim.md").read_text()
    assert "NAV_RCL_ACT" in text
    assert "does not write" in text
    assert "NAV_RCL_ACT: 0" in text  # names the sample value we refuse
    assert "Keep `NAV_RCL_ACT` untouched" in text or "NAV_RCL_ACT` untouched" in text
    grok = (REPO / "GROK.md").read_text()
    assert "do not write" in grok.lower() or "Do not write" in grok
    assert "NAV_RCL_ACT" in grok
    assert "still open on #19" not in grok


def test_airsim_doc_ffmpeg_is_sih_only():
    """Gazebo compose has no ffmpeg/smoke.mp4; SIH alone runs the file loop."""
    text = (REPO / "docs/sitl-airsim.md").read_text()
    assert "SIH-only" in text or "ffmpeg** (file loop)" in text or "ffmpeg** (file loop)" in text
    assert "no** ffmpeg" in text.lower() or "no ffmpeg" in text.lower() or "**no** ffmpeg" in text
    gz = (REPO / "compose.gazebo.yaml").read_text()
    assert "ffmpeg" not in gz.lower() or "No bare ffmpeg" in gz or "no bare ffmpeg" in gz.lower()
    # compose.gazebo comment mentions ffmpeg negatively; service must not be rtsp-pub
    assert "rtsp-pub" not in gz
    assert "mwader/static-ffmpeg" not in gz


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
