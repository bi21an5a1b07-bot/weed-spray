"""Nadir pixel → local north/east. Numbers are hand-calculated. No MAVSDK."""

import pytest

from weed_spray.vision.project import project_nadir

# 640x480, HFOV 90°. tan(45°)=1 so fx = 320. Square pixels ⇒ fy = 320.
# 32 px right of center at 2.0 m AGL is 2 * 32/320 = 0.2 m to image-right.
# Image-right is body-right: +east when heading is 0 (nose north).
# Image-down is aft: -north when heading is 0.


def test_image_center_is_vehicle_ned_at_any_heading():
    for heading in (0.0, 90.0, 180.0, -20.0):
        point = project_nadir(
            cx=0.5,
            cy=0.5,
            frame_w=640,
            frame_h=480,
            hfov_deg=90.0,
            height_m=2.0,
            north_m=10.0,
            east_m=4.0,
            heading_deg=heading,
        )
        assert point == pytest.approx((10.0, 4.0))


def test_image_right_is_east_when_heading_is_zero():
    point = project_nadir(
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
    assert point == pytest.approx((10.0, 4.2))


def test_heading_90_rotates_image_right_to_south():
    # Nose east: body-right points south, so +0.2 m image-right is -0.2 m north.
    point = project_nadir(
        cx=0.5 + 32 / 640,
        cy=0.5,
        frame_w=640,
        frame_h=480,
        hfov_deg=90.0,
        height_m=2.0,
        north_m=10.0,
        east_m=4.0,
        heading_deg=90.0,
    )
    assert point == pytest.approx((9.8, 4.0))


def test_image_down_is_aft_when_heading_is_zero():
    point = project_nadir(
        cx=0.5,
        cy=0.5 + 32 / 480,
        frame_w=640,
        frame_h=480,
        hfov_deg=90.0,
        height_m=2.0,
        north_m=10.0,
        east_m=4.0,
        heading_deg=0.0,
    )
    assert point == pytest.approx((9.8, 4.0))


def test_missing_height_or_fov_is_none():
    kwargs = dict(
        cx=0.5,
        cy=0.5,
        frame_w=640,
        frame_h=480,
        north_m=0.0,
        east_m=0.0,
        heading_deg=0.0,
    )
    assert project_nadir(hfov_deg=90.0, height_m=None, **kwargs) is None
    assert project_nadir(hfov_deg=None, height_m=2.0, **kwargs) is None
    assert project_nadir(hfov_deg=90.0, height_m=0.0, **kwargs) is None


def test_center_outside_frame_is_none():
    assert (
        project_nadir(
            cx=1.2,
            cy=0.5,
            frame_w=640,
            frame_h=480,
            hfov_deg=90.0,
            height_m=2.0,
            north_m=0.0,
            east_m=0.0,
            heading_deg=0.0,
        )
        is None
    )


def test_point_outside_fence_is_none():
    # Image-right 0.2 m from the origin lands at east 0.2, past the east edge 0.1.
    point = project_nadir(
        cx=0.5 + 32 / 640,
        cy=0.5,
        frame_w=640,
        frame_h=480,
        hfov_deg=90.0,
        height_m=2.0,
        north_m=0.0,
        east_m=0.0,
        heading_deg=0.0,
        fence=(1.0, -1.0, 0.1, -1.0),
    )
    assert point is None


def test_fence_edge_is_inside_despite_tan_float():
    """Hand-calc 0.2 m east must sit on the fence edge, not trip float >.

    tan(π/4) float makes fx ≈ 320.00000000000006 so east ≈ 0.20000000000000015.
    Docstring: the edge itself is inside.
    """
    point = project_nadir(
        cx=0.5 + 32 / 640,
        cy=0.5,
        frame_w=640,
        frame_h=480,
        hfov_deg=90.0,
        height_m=2.0,
        north_m=0.0,
        east_m=0.0,
        heading_deg=0.0,
        fence=(1.0, -1.0, 0.2, -1.0),
    )
    assert point is not None
    assert point == pytest.approx((0.0, 0.2), abs=1e-9)
