"""Pixel observations from a detector stand-in. Does not import Ultralytics.

Class ids follow ``weed_spray.vision.classes``. Rows are image-plane only:
no north/east, so a file-loop box cannot become a spray point.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from weed_spray.vision.classes import NAMES

MIN_SHORT_SIDE_PX = 20
"""Skip a box whose short side is under this many pixels at ``imgsz``."""


@dataclass(frozen=True)
class RawBox:
    """One detector box before the class, confidence, and size filters.

    Attributes:
        class_id: YOLO class index. Only ids in ``NAMES`` are kept.
        conf: Detector confidence, typically 0-1.
        cx: Box center x as a fraction of the frame width (0-1).
        cy: Box center y as a fraction of the frame height (0-1).
        w: Box width as a fraction of the frame width (0-1).
        h: Box height as a fraction of the frame height (0-1).
    """

    class_id: int
    conf: float
    cx: float
    cy: float
    w: float
    h: float


def parse_boxes(
    boxes: Sequence[RawBox],
    *,
    conf_min: float,
    imgsz: int,
) -> list[dict[str, float | str]]:
    """Keep in-map boxes at or above ``conf_min`` whose short side is ≥ 20 px.

    Short side is ``min(w, h) * imgsz`` (the inference image, not the file
    resolution). Unknown class indexes are dropped, not remapped. The dict
    key is ``class`` (the string name). There is no ``north_m`` or ``east_m``.

    Args:
        boxes: Detector rows. An empty sequence returns ``[]``.
        conf_min: Drop rows with ``conf`` strictly below this.
        imgsz: Inference image side in pixels. Used only for the 20 px rule.

    Returns:
        Pixel rows ``{class, conf, cx, cy, w, h}`` in input order.
    """
    kept: list[dict[str, float | str]] = []
    for box in boxes:
        name = NAMES.get(box.class_id)
        if name is None or box.conf < conf_min:
            continue
        short_px = min(box.w, box.h) * imgsz
        if short_px < MIN_SHORT_SIDE_PX:
            continue
        kept.append(
            {
                "class": name,
                "conf": box.conf,
                "cx": box.cx,
                "cy": box.cy,
                "w": box.w,
                "h": box.h,
            }
        )
    return kept
