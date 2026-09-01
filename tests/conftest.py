"""Shared pytest fixtures. No live PX4 -- see tests/fakes.py."""

import pytest

from weed_spray.vision import main as vision_main


@pytest.fixture(autouse=True)
def _reset_vision_boxes():
    """Clear the in-memory injector list so tests cannot leak boxes."""
    vision_main._boxes.clear()
    yield
    vision_main._boxes.clear()
