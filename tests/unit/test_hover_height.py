"""Spray hover sits above S500 / gz x500 landing gear (TDD)."""

import pytest

from weed_spray.backend.config import Settings

# gz x500_base skid collision z=-0.2195 m; S500 CF gear is the same class.
LANDING_GEAR_AGL_M = 0.22
# ~2 in above the skids so props/lidar/nozzle are not in the gear.
HOVER_CLEARANCE_M = 0.05


def test_commanded_hover_is_gear_plus_two_inches():
    """Default hover_agl_m is S500/gz x500 gear (~0.22 m) plus ~2 in."""
    s = Settings()
    assert s.hover_agl_m == LANDING_GEAR_AGL_M + HOVER_CLEARANCE_M
    assert s.hover_agl_m == 0.27


def test_backend_gz_does_not_double_count_lidar_mount():
    """gz lidar tracks NED 1:1; Makefile must not add WEED_LIDAR_MOUNT_DOWN_M=0.28 (#33)."""
    from pathlib import Path

    text = Path(__file__).resolve().parents[2].joinpath("Makefile").read_text()
    assert "WEED_LIDAR_MOUNT_DOWN_M=0.28" not in text


def test_ned_down_for_lidar_band_descends_when_too_high():
    """Lidar 0.55 m with NED -0.55 must nudge toward the 0.24-0.32 m band (#33)."""
    from weed_spray.backend.vehicle import ned_down_for_lidar_band

    down = ned_down_for_lidar_band(-0.55, 0.55, 0.24, 0.32)
    assert 0.24 <= abs(down) <= 0.32


def test_ned_down_for_lidar_band_climbs_when_too_low():
    """Lidar 0.19 m with NED -0.27 must climb toward the band (#33)."""
    from weed_spray.backend.vehicle import ned_down_for_lidar_band

    down = ned_down_for_lidar_band(-0.27, 0.19, 0.24, 0.32)
    assert abs(down) >= 0.24
    assert abs(down) <= 0.40


def test_ned_hover_accounts_for_lidar_mount_below_cg():
    """NED down is -(hover_agl_m + lidar_mount_down_m) so lidar, not CG, is at hover."""
    s = Settings(hover_agl_m=0.27, lidar_mount_down_m=0.28)
    down_hover = -(s.hover_agl_m + s.lidar_mount_down_m)
    assert down_hover == -0.55


def test_accept_band_stays_above_landing_gear():
    """Accept min stays above gear; commanded hover sits inside the band."""
    s = Settings()
    assert s.hover_min_m > LANDING_GEAR_AGL_M
    assert s.hover_min_m <= s.hover_agl_m <= s.hover_max_m
    assert s.hover_min_m == 0.24
    assert s.hover_max_m == 0.32


def test_stuck_lidar_does_not_restack_ned_nudge():
    """Same out-of-band lidar must not re-apply full error every poll (BugScout #34)."""
    from weed_spray.backend.vehicle import ned_down_for_lidar_band, should_nudge_for_lidar_band

    down = -0.55
    last_nudged: float | None = None
    downs: list[float] = []
    for _ in range(4):
        lidar = 0.55
        if should_nudge_for_lidar_band(lidar, 0.24, 0.32, last_nudged):
            down = ned_down_for_lidar_band(down, lidar, 0.24, 0.32)
            last_nudged = lidar
        downs.append(down)
    assert downs[0] == pytest.approx(-0.28)
    assert downs == [downs[0]] * 4


def test_partial_descent_does_not_restack_ned_nudge():
    """After one nudge, a changing out-of-band lidar must not re-add full error (#34).

    lidar 0.55 → down -0.28; 0.50 then 0.45 must keep -0.28, not walk to +0.11.
    """
    from weed_spray.backend.vehicle import ned_down_for_lidar_band, should_nudge_for_lidar_band

    down = -0.55
    last_nudged: float | None = None
    downs: list[float] = []
    for lidar in (0.55, 0.50, 0.45, 0.40):
        if should_nudge_for_lidar_band(lidar, 0.24, 0.32, last_nudged):
            down = ned_down_for_lidar_band(down, lidar, 0.24, 0.32)
            last_nudged = lidar
        downs.append(down)
    assert downs[0] == pytest.approx(-0.28)
    assert downs == [downs[0]] * 4


def test_after_first_nudge_later_readings_wait():
    """First out-of-band reading may nudge; later readings wait (no restack)."""
    from weed_spray.backend.vehicle import should_nudge_for_lidar_band

    assert should_nudge_for_lidar_band(0.55, 0.24, 0.32, None) is True
    assert should_nudge_for_lidar_band(0.55, 0.24, 0.32, 0.55) is False
    assert should_nudge_for_lidar_band(0.40, 0.24, 0.32, 0.55) is False
    assert should_nudge_for_lidar_band(0.28, 0.24, 0.32, 0.55) is False
