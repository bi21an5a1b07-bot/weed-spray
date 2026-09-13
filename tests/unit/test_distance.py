"""distance_reading_m: NaN, non-positive, junk, and SIH relative-alt mirrors → None."""

import math

from weed_spray.backend.vehicle import distance_reading_m


def test_valid_range():
    assert distance_reading_m(0.22) == 0.22
    assert distance_reading_m(12) == 12.0


def test_missing_and_nan():
    assert distance_reading_m(None) is None
    assert distance_reading_m(float("nan")) is None
    assert distance_reading_m(math.nan) is None
    assert distance_reading_m(0) is None
    assert distance_reading_m(-1) is None
    assert distance_reading_m("nope") is None


def test_sih_mirror_of_relative_alt_is_missing():
    """px4 SIH can publish DISTANCE_SENSOR ≈ relative_alt; that is not a lidar."""
    assert distance_reading_m(11.97, relative_alt_m=12.0) is None
    assert distance_reading_m(29.68, relative_alt_m=29.93) is None


def test_real_low_hover_lidar_kept_even_if_near_relative_alt():
    """Spray hover ~0.22 m: real lidar may match relative_alt; do not drop it."""
    assert distance_reading_m(0.22, relative_alt_m=0.21) == 0.22
    assert distance_reading_m(0.28, relative_alt_m=0.30) == 0.28


def test_unrelated_high_reading_kept_without_relative_alt():
    assert distance_reading_m(11.97, relative_alt_m=None) == 11.97
