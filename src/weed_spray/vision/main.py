"""Detection injector / YOLO stub on :8090. Injected boxes are the v1 pass."""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

from weed_spray.vision.classes import CLASSES, NAMES
from weed_spray.vision.reader import drive_rtsp, env_reader_settings
from weed_spray.vision.runtime import (
    attach_reader,
    configure_logging,
    note_configured_weights,
    reader_view,
)

log = logging.getLogger("weed_spray.vision")

app = FastAPI(title="weed-spray-vision")
_boxes: list[dict[str, Any]] = []


class Detection(BaseModel):
    """One injected plant. ``class`` must be in the class map (incl. mallow)."""

    id: str
    class_name: str = Field(alias="class")
    north_m: float
    east_m: float
    conf: float = 1.0

    model_config = {"populate_by_name": True}

    @field_validator("class_name")
    @classmethod
    def known_class(cls, value: str) -> str:
        """Reject crabgrass / other_weed / anything not in the frozen map."""
        if value not in CLASSES:
            raise ValueError(f"class must be one of {sorted(CLASSES)}")
        return value


class InjectRequest(BaseModel):
    """POST /inject body."""

    detections: list[Detection]


@app.get("/health")
async def health():
    """Liveness. A missing weights file stays injector. An attached reader is ``yolo``."""
    note_configured_weights()
    view = reader_view()
    if view is None:
        return {
            "ok": True,
            "mode": "injector",
            "count": len(_boxes),
            "names": NAMES,
            "weights": None,
        }
    return {
        "ok": True,
        "mode": "yolo",
        "count": len(view["rows"]),
        "names": NAMES,
        "weights": view["weights"],
        "camera": view["camera"],
    }


@app.get("/detections")
async def detections():
    """Injector boxes, or the latest pixel rows when a YOLO reader is attached."""
    view = reader_view()
    if view is not None:
        return {"detections": view["rows"]}
    return {"detections": _boxes}


@app.post("/inject")
async def inject(req: InjectRequest):
    """Upsert boxes by id. Does not confirm spray."""
    global _boxes
    incoming = [d.model_dump(by_alias=True) for d in req.detections]
    by_id = {b["id"]: b for b in _boxes}
    for item in incoming:
        by_id[item["id"]] = item
    _boxes = list(by_id.values())
    log.info("injected %s", [b["id"] for b in incoming])
    return {"detections": _boxes}


@app.delete("/detections")
async def clear():
    """Drop all injected boxes."""
    _boxes.clear()
    return {"detections": []}


def _open_yolo_if_configured() -> None:
    """If weights exist, serve YOLO mode. Import Ultralytics only in that branch.

    A missing extra leaves the process up with ``camera`` false and no boxes.
    A present extra starts one daemon RTSP reader. Georeference is not this
    process: rows stay pixels.
    """
    raw = os.environ.get("WEED_YOLO_WEIGHTS", "").strip()
    if not raw or not Path(raw).is_file():
        return
    try:
        import ultralytics  # noqa: F401  import only when a weights file exists
    except ImportError:
        log.info("ultralytics is not installed (uv sync --extra yolo); camera down")
        attach_reader(weights=raw, rows=[], camera_ok=False)
        return

    url, conf, imgsz, device = env_reader_settings()
    attach_reader(weights=raw, rows=[], camera_ok=True)

    def _thread() -> None:
        def publish(rows: list[dict]) -> None:
            attach_reader(weights=raw, rows=rows, camera_ok=True)

        status = drive_rtsp(
            raw,
            url,
            publish=publish,
            conf_min=conf,
            imgsz=imgsz,
            device=device,
        )
        if not status.ok:
            log.info("camera down: %s", status.error)
            attach_reader(weights=raw, rows=[], camera_ok=False)

    threading.Thread(target=_thread, name="yolo-rtsp", daemon=True).start()


def run() -> None:
    """CLI entry ``weed-spray-vision``."""
    configure_logging()
    _open_yolo_if_configured()
    uvicorn.run(
        "weed_spray.vision.main:app",
        host="127.0.0.1",
        port=8090,
        reload=False,
    )


if __name__ == "__main__":
    run()
