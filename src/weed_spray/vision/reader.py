"""Turn frames into pixel rows. The Ultralytics import stays inside the RTSP adapter."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from weed_spray.vision.boxes import RawBox, parse_boxes


@dataclass(frozen=True)
class Frame:
    """One decoded image plus the size the box fractions refer to.

    Attributes:
        image: Opaque frame for the predictor. Tests use a string.
        width: Frame width in pixels.
        height: Frame height in pixels.
        t: Capture timestamp string.
    """

    image: object
    width: int
    height: int
    t: str


@dataclass(frozen=True)
class CameraStatus:
    """Whether the frame loop finished cleanly.

    Attributes:
        ok: False when the camera or predictor raised.
        error: The exception string, or None on success.
    """

    ok: bool
    error: str | None = None


def consume_frames(
    frames: Iterable[Frame],
    predict: Callable[[Frame], list[RawBox]],
    *,
    publish: Callable[[list[dict]], None],
    conf_min: float,
    imgsz: int,
) -> CameraStatus:
    """Publish pixel rows for each frame. A later frame replaces the previous list.

    On any exception, publish ``[]`` and return ``ok=False`` instead of raising.
    Rows have no north/east.

    Args:
        frames: Decoded frames. Not opened here.
        predict: Maps one frame to raw detector boxes.
        publish: Called with the latest row list, including ``[]`` on failure.
        conf_min: Drop boxes below this.
        imgsz: Inference size for the 20 px rule.

    Returns:
        Camera status. Success is ``ok=True``.
    """
    try:
        for frame in frames:
            rows = parse_boxes(predict(frame), conf_min=conf_min, imgsz=imgsz)
            for row in rows:
                row["frame_w"] = frame.width
                row["frame_h"] = frame.height
                row["frame_t"] = frame.t
            publish(list(rows))
    except Exception as exc:  # noqa: BLE001  a dead camera must not kill the process
        publish([])
        return CameraStatus(ok=False, error=str(exc))
    return CameraStatus(ok=True)


def drive_rtsp(
    weights: str,
    url: str,
    *,
    publish: Callable[[list[dict]], None],
    conf_min: float,
    imgsz: int,
    device: str,
) -> CameraStatus:
    """Pull ``url`` with Ultralytics ``predict(stream=True)`` at about 5 Hz.

    Imports ultralytics only when called. A camera or model error becomes
    ``CameraStatus(ok=False)`` via ``consume_frames``.

    Args:
        weights: Path to a YOLO ``.pt`` file.
        url: RTSP URL, normally ``rtsp://127.0.0.1:8554/cam``.
        publish: Latest pixel rows.
        conf_min: Detector confidence floor.
        imgsz: Inference size.
        device: Ultralytics device string (``cpu`` or ``0``).

    Returns:
        Camera status after the stream ends or fails.
    """
    try:
        from ultralytics import YOLO

        model = YOLO(weights)
    except Exception as exc:  # noqa: BLE001  bad weights must not kill the daemon
        publish([])
        return CameraStatus(ok=False, error=str(exc))

    pending: list[RawBox] = []
    last = 0.0

    def frames() -> Iterable[Frame]:
        nonlocal last
        for result in model.predict(
            source=url,
            stream=True,
            imgsz=imgsz,
            conf=conf_min,
            device=device,
            verbose=False,
        ):
            now = time.monotonic()
            if now - last < 0.2:
                continue
            last = now
            pending.clear()
            boxes = getattr(result, "boxes", None)
            if boxes is not None:
                for box in boxes:
                    xywhn = box.xywhn[0].tolist()
                    pending.append(
                        RawBox(
                            class_id=int(box.cls[0]),
                            conf=float(box.conf[0]),
                            cx=float(xywhn[0]),
                            cy=float(xywhn[1]),
                            w=float(xywhn[2]),
                            h=float(xywhn[3]),
                        )
                    )
            shape = result.orig_shape
            height, width = int(shape[0]), int(shape[1])
            yield Frame(
                image=getattr(result, "orig_img", None),
                width=width,
                height=height,
                t=datetime.now(UTC).isoformat(),
            )

    def predict(_frame: Frame) -> list[RawBox]:
        return list(pending)

    return consume_frames(frames(), predict, publish=publish, conf_min=conf_min, imgsz=imgsz)


def env_reader_settings() -> tuple[str, float, int, str]:
    """``(rtsp_url, conf, imgsz, device)`` from ``WEED_*`` with injector-safe defaults."""
    url = os.environ.get("WEED_RTSP_URL", "").strip() or "rtsp://127.0.0.1:8554/cam"
    conf_raw = os.environ.get("WEED_YOLO_CONF", "").strip()
    imgsz_raw = os.environ.get("WEED_YOLO_IMGSZ", "").strip()
    device = os.environ.get("WEED_YOLO_DEVICE", "").strip() or "cpu"
    conf = float(conf_raw) if conf_raw else 0.5
    imgsz = int(imgsz_raw) if imgsz_raw else 640
    return url, conf, imgsz, device
