"""YOLO frame loop with a fake predictor. No Ultralytics and no RTSP."""

from weed_spray.vision.boxes import RawBox
from weed_spray.vision.reader import Frame, consume_frames


def test_second_frame_replaces_the_first():
    frames = [
        Frame(image="a", width=640, height=480, t="t0"),
        Frame(image="b", width=800, height=600, t="t1"),
    ]
    batches = [
        [RawBox(class_id=0, conf=0.9, cx=0.5, cy=0.5, w=0.2, h=0.2)],
        [RawBox(class_id=1, conf=0.8, cx=0.2, cy=0.3, w=0.4, h=0.4)],
    ]

    def predict(frame: Frame) -> list[RawBox]:
        return batches[frames.index(frame)]

    seen: list[list[dict]] = []
    consume_frames(frames, predict, publish=seen.append, conf_min=0.5, imgsz=640)
    assert [row["class"] for row in seen[0]] == ["dandelion"]
    assert [row["class"] for row in seen[1]] == ["clover"]
    assert "north_m" not in seen[1][0]
    assert seen[1][0]["frame_w"] == 800
    assert seen[1][0]["frame_h"] == 600
    assert seen[1][0]["frame_t"] == "t1"


def test_camera_failure_clears_boxes_and_does_not_raise():
    def frames():
        yield Frame(image="a", width=640, height=480, t="t0")
        raise ConnectionError("rtsp closed")

    def predict(_frame: Frame) -> list[RawBox]:
        return [RawBox(class_id=0, conf=0.9, cx=0.5, cy=0.5, w=0.2, h=0.2)]

    seen: list[list[dict]] = []
    camera = consume_frames(frames(), predict, publish=seen.append, conf_min=0.5, imgsz=640)
    assert camera.ok is False
    assert camera.error == "rtsp closed"
    assert seen[-1] == []
