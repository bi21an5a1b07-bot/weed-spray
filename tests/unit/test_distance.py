"""distance_reading_m: NaN, non-positive, and junk become None (SIH has no lidar)."""

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
