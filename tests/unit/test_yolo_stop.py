"""Reader teardown must clear sticky YOLO rows (PR #54 follow-up)."""

from weed_spray.vision import runtime
from weed_spray.vision.main import clear_reader_after_drive
from weed_spray.vision.reader import CameraStatus


def test_clear_reader_after_drive_clears_even_when_ok(tmp_path):
    weights = str(tmp_path / "best.pt")
    runtime.reset_for_tests()
    runtime.attach_reader(
        weights=weights,
        rows=[{"class": "dandelion", "conf": 0.9, "cx": 0.5, "cy": 0.5, "w": 0.2, "h": 0.2}],
        camera_ok=True,
    )
    clear_reader_after_drive(weights=weights, status=CameraStatus(ok=True))
    view = runtime.reader_view()
    assert view is not None
    assert view["camera"] is False
    assert view["rows"] == []


def test_clear_reader_after_drive_clears_on_error(tmp_path):
    weights = str(tmp_path / "best.pt")
    runtime.reset_for_tests()
    runtime.attach_reader(
        weights=weights,
        rows=[{"class": "clover", "conf": 0.8, "cx": 0.2, "cy": 0.3, "w": 0.1, "h": 0.1}],
        camera_ok=True,
    )
    clear_reader_after_drive(weights=weights, status=CameraStatus(ok=False, error="rtsp closed"))
    view = runtime.reader_view()
    assert view is not None
    assert view["camera"] is False
    assert view["rows"] == []
