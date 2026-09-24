"""Pixel observations from a detector stand-in. No Ultralytics and no RTSP."""

from weed_spray.vision.boxes import RawBox, parse_boxes


def test_maps_frozen_class_ids():
    boxes = [
        RawBox(class_id=0, conf=0.9, cx=0.5, cy=0.5, w=0.2, h=0.2),
        RawBox(class_id=1, conf=0.9, cx=0.4, cy=0.4, w=0.2, h=0.2),
        RawBox(class_id=2, conf=0.9, cx=0.3, cy=0.3, w=0.2, h=0.2),
        RawBox(class_id=3, conf=0.9, cx=0.2, cy=0.2, w=0.2, h=0.2),
    ]
    out = parse_boxes(boxes, conf_min=0.5, imgsz=640)
    assert [row["class"] for row in out] == ["dandelion", "clover", "thistle", "mallow"]


def test_drops_unknown_class_index():
    out = parse_boxes(
        [RawBox(class_id=4, conf=0.99, cx=0.5, cy=0.5, w=0.2, h=0.2)],
        conf_min=0.5,
        imgsz=640,
    )
    assert out == []


def test_drops_confidence_below_threshold():
    out = parse_boxes(
        [RawBox(class_id=0, conf=0.49, cx=0.5, cy=0.5, w=0.2, h=0.2)],
        conf_min=0.5,
        imgsz=640,
    )
    assert out == []


def test_keeps_confidence_equal_to_threshold():
    out = parse_boxes(
        [RawBox(class_id=0, conf=0.5, cx=0.5, cy=0.5, w=0.2, h=0.2)],
        conf_min=0.5,
        imgsz=640,
    )
    assert len(out) == 1
    assert out[0]["conf"] == 0.5


def test_drops_short_side_under_20px_at_imgsz():
    # 19 px on the short side at 640: 19/640.
    out = parse_boxes(
        [RawBox(class_id=0, conf=0.9, cx=0.5, cy=0.5, w=0.2, h=19 / 640)],
        conf_min=0.5,
        imgsz=640,
    )
    assert out == []


def test_keeps_short_side_of_exactly_20px():
    out = parse_boxes(
        [RawBox(class_id=2, conf=0.8, cx=0.5, cy=0.5, w=0.4, h=20 / 640)],
        conf_min=0.5,
        imgsz=640,
    )
    assert len(out) == 1
    assert out[0]["class"] == "thistle"


def test_empty_result_is_empty_list():
    assert parse_boxes([], conf_min=0.5, imgsz=640) == []


def test_row_is_pixels_only():
    out = parse_boxes(
        [RawBox(class_id=0, conf=0.9, cx=0.1, cy=0.2, w=0.3, h=0.4)],
        conf_min=0.5,
        imgsz=640,
    )
    assert set(out[0]) == {"class", "conf", "cx", "cy", "w", "h"}
    assert out[0]["cx"] == 0.1
    assert out[0]["cy"] == 0.2
    assert out[0]["w"] == 0.3
    assert out[0]["h"] == 0.4
