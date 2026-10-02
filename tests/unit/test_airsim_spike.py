"""Issue #66 AirSim spike contracts. No live Unreal, PX4, or Docker."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Endorsement patterns that must stay absent (BugScout #68 reviews 5388013477 / 5388034803).
_DOCKER_AS_AIRSIM_PROOF = (
    re.compile(r"(?i)px4io[^\n]{0,100}(?:can|may|should|will)\s+prove"),
    re.compile(r"(?i)(?:can|may|should)\s+prove[^\n]{0,80}(?:AirSim|TCP\s*\*?\*?4560)"),
    re.compile(r"(?i)or the existing `?px4io"),
    re.compile(
        r"(?i)(?<!do not )treat Docker SITL as the AirSim PX4 proof"
    ),
    re.compile(
        r"(?i)(?:via|using|with)\s+(?:the\s+)?`?px4io`?[^\n]{0,60}"
        r"(?:Docker\s+)?images?[^\n]{0,40}(?:AirSim|TCP\s*\*?\*?4560)"
    ),
)

_NAV_RCL_ACT_ENDORSE = (
    re.compile(
        r"(?i)(?:operators?|you|we)\s+should\s+"
        r"(?:set|write|copy|use|apply)\s+`?NAV_RCL_ACT"
    ),
    re.compile(
        r"(?i)(?:should|must)\s+(?:set|write|copy|use|apply)\s+`?NAV_RCL_ACT"
        r"`?\s*[:=]\s*0"
    ),
    re.compile(
        r"(?i)(?:copy|write|apply)\s+`?NAV_RCL_ACT`?\s*[:=]\s*0"
        r"(?![^\n]{0,120}does not write)"
    ),
    re.compile(
        r"(?i)recommend(?:s|ed)?\s+[^\n]{0,40}NAV_RCL_ACT`?\s*[:=]\s*0"
    ),
)


def _assert_absent(patterns: tuple[re.Pattern[str], ...], text: str, label: str) -> None:
    for pat in patterns:
        m = pat.search(text)
        assert m is None, f"{label} endorsement matched {pat.pattern!r} at {m.group(0)!r}"


def test_airsim_spike_doc_locks_topology_and_recommendation():
    """Spike doc keeps SIH/Gazebo default; AirSim is not a replacement."""
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
    """AirSim TCP 4560 needs source-built none_*; Docker px4io is not a proof path."""
    text = (REPO / "docs/sitl-airsim.md").read_text()
    # Anchored refuse (one sentence binds Docker images ↔ will not attach ↔ not proof).
    assert (
        "The existing `px4io/px4-sitl` and `px4io/px4-sitl-gazebo` images start "
        "**embedded** SIH/Gazebo and **will not** attach to AirSim — do not treat "
        "Docker SITL as the AirSim PX4 proof."
    ) in text
    assert (
        "AirSim attaches over TCP **4560** to a **source-built** "
        "`make px4_sitl none_*` (external sim)."
    ) in text
    assert (
        "Source-built `px4_sitl none_*` + TCP 4560; "
        "Docker SIH/Gazebo images will not attach"
    ) in text
    assert (
        "Prove current PX4 as **source-built** `px4_sitl none_*` "
        "(not only v1.12.3) against AirSim TCP 4560 — not via `px4io` Docker images."
    ) in text
    _assert_absent(_DOCKER_AS_AIRSIM_PROOF, text, "Docker/px4io-as-AirSim-proof")
    # Guard: these patterns must catch BugScout's decoy failure mode.
    decoy = (
        text.replace(
            "do not treat Docker SITL as the AirSim PX4 proof",
            "px4io images can prove AirSim TCP 4560",
        )
        + "\nDecoy: will not attach somewhere else.\n"
    )
    hits = [p for p in _DOCKER_AS_AIRSIM_PROOF if p.search(decoy)]
    assert hits, "negative patterns must fail if Docker is re-endorsed as TCP 4560 proof"


def test_airsim_doc_refuses_nav_rcl_act_zero():
    """Repo must refuse copying AirSim sample NAV_RCL_ACT: 0 into our stack."""
    text = (REPO / "docs/sitl-airsim.md").read_text()
    # Anchored refuse binds "does not write" to NAV_RCL_ACT (not a loose token).
    assert (
        "This repo **does not write** `NAV_RCL_ACT` or `COM_RCL_EXCEPT` bit 2"
    ) in text
    assert "- [ ] Keep `NAV_RCL_ACT` untouched." in text
    # Sample value may be named; endorsement of writing/setting it must not appear.
    assert "`NAV_RCL_ACT: 0`" in text
    _assert_absent(_NAV_RCL_ACT_ENDORSE, text, "NAV_RCL_ACT:0")

    grok = (REPO / "GROK.md").read_text()
    assert (
        "Do not write `COM_RCL_EXCEPT` bit 2 or disable `NAV_RCL_ACT`."
    ) in grok
    assert "still open on #19" not in grok
    _assert_absent(_NAV_RCL_ACT_ENDORSE, grok, "GROK NAV_RCL_ACT:0")
    # Guard: endorsement must trip negatives even if refuse substrings remain.
    endorse = (
        text
        + "\nOperators should set `NAV_RCL_ACT: 0` like AirSim samples.\n"
    )
    hits = [p for p in _NAV_RCL_ACT_ENDORSE if p.search(endorse)]
    assert hits, "negative patterns must fail if docs tell operators to set NAV_RCL_ACT: 0"


def test_airsim_doc_ffmpeg_is_sih_only():
    """Gazebo compose has no ffmpeg/smoke.mp4; SIH alone runs the file loop."""
    text = (REPO / "docs/sitl-airsim.md").read_text()
    assert "SIH-only" in text or "ffmpeg** (file loop)" in text
    assert (
        "no** ffmpeg" in text.lower()
        or "no ffmpeg" in text.lower()
        or "**no** ffmpeg" in text
    )
    gz = (REPO / "compose.gazebo.yaml").read_text()
    assert (
        "ffmpeg" not in gz.lower()
        or "No bare ffmpeg" in gz
        or "no bare ffmpeg" in gz.lower()
    )
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
