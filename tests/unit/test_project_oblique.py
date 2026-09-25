"""Forward-down pixel projection and arrival time. Hand-calculated. No PX4."""

import math

import pytest

from weed_spray.vision.project import arrival_time_s, project_nadir, project_oblique

# 15° below the horizon, height 2 m. Forward offset is 2 / tan(15°).
_FORWARD_15 = 2.0 / math.tan(math.radians(15.0))


def test_tilt_90_center_matches_nadir():
    kwargs = dict(
        cx=0.5,
        cy=0.5,
        frame_w=640,
        frame_h=480,
        hfov_deg=90.0,
        height_m=2.0,
        north_m=10.0,
        east_m=4.0,
        heading_deg=20.0,
    )
    assert project_oblique(tilt_deg=90.0, **kwargs) == pytest.approx(project_nadir(**kwargs))


def test_tilt_90_image_right_matches_nadir():
    kwargs = dict(
        cx=0.5 + 32 / 640,
        cy=0.5,
        frame_w=640,
        frame_h=480,
        hfov_deg=90.0,
        height_m=2.0,
        north_m=10.0,
        east_m=4.0,
        heading_deg=0.0,
    )
    assert project_oblique(tilt_deg=90.0, **kwargs) == pytest.approx((10.0, 4.2))
    assert project_oblique(tilt_deg=90.0, **kwargs) == pytest.approx(project_nadir(**kwargs))


def test_center_pixel_is_ahead_by_h_over_tan_tilt():
    point = project_oblique(
        cx=0.5,
        cy=0.5,
        frame_w=640,
        frame_h=480,
        hfov_deg=90.0,
        tilt_deg=15.0,
        height_m=2.0,
        north_m=10.0,
        east_m=4.0,
        heading_deg=0.0,
    )
    assert point == pytest.approx((10.0 + _FORWARD_15, 4.0))


def test_heading_90_rotates_the_forward_offset_east():
    point = project_oblique(
        cx=0.5,
        cy=0.5,
        frame_w=640,
        frame_h=480,
        hfov_deg=90.0,
        tilt_deg=15.0,
        height_m=2.0,
        north_m=10.0,
        east_m=4.0,
        heading_deg=90.0,
    )
    assert point == pytest.approx((10.0, 4.0 + _FORWARD_15))


def test_missing_height_tilt_or_hfov_is_none():
    kwargs = dict(
        cx=0.5,
        cy=0.5,
        frame_w=640,
        frame_h=480,
        north_m=0.0,
        east_m=0.0,
        heading_deg=0.0,
    )
    assert project_oblique(hfov_deg=90.0, tilt_deg=15.0, height_m=None, **kwargs) is None
    assert project_oblique(hfov_deg=90.0, tilt_deg=None, height_m=2.0, **kwargs) is None
    assert project_oblique(hfov_deg=None, tilt_deg=15.0, height_m=2.0, **kwargs) is None


def test_horizontal_ray_misses_the_ground():
    assert (
        project_oblique(
            cx=0.5,
            cy=0.5,
            frame_w=640,
            frame_h=480,
            hfov_deg=90.0,
            tilt_deg=0.0,
            height_m=2.0,
            north_m=0.0,
            east_m=0.0,
            heading_deg=0.0,
        )
        is None
    )


def test_arrival_time_is_distance_over_closing_speed():
    # Plant 10 m north, closing at 2 m/s.
    assert arrival_time_s(
        north_m=0.0,
        east_m=0.0,
        plant_north_m=10.0,
        plant_east_m=0.0,
        vn_m_s=2.0,
        ve_m_s=0.0,
    ) == pytest.approx(5.0)


def test_stopped_or_receding_has_no_arrival_time():
    assert (
        arrival_time_s(
            north_m=0.0,
            east_m=0.0,
            plant_north_m=10.0,
            plant_east_m=0.0,
            vn_m_s=0.0,
            ve_m_s=0.0,
        )
        is None
    )
    assert (
        arrival_time_s(
            north_m=0.0,
            east_m=0.0,
            plant_north_m=10.0,
            plant_east_m=0.0,
            vn_m_s=-1.0,
            ve_m_s=0.0,
        )
        is None
    )


def test_already_there_is_zero_seconds():
    assert arrival_time_s(
        north_m=3.0,
        east_m=4.0,
        plant_north_m=3.0,
        plant_east_m=4.0,
        vn_m_s=0.0,
        ve_m_s=0.0,
    ) == pytest.approx(0.0)
