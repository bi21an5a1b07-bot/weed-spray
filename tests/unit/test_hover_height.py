"""Spray hover sits above S500 / gz x500 landing gear (TDD)."""

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
