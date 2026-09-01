"""Detection injector / YOLO stub on :8090. Injected boxes are the v1 pass."""

from __future__ import annotations

import logging
from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

from weed_spray.vision.classes import CLASSES, NAMES

log = logging.getLogger("weed_spray.vision")

app = FastAPI(title="weed-spray-vision")
_boxes: list[dict[str, Any]] = []


class Detection(BaseModel):
    """One injected plant. ``class`` must be dandelion, clover, or thistle."""

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
    """Liveness; ``names`` is the frozen id→class map. ``weights`` is None in v1."""
    return {
        "ok": True,
        "mode": "injector",
        "count": len(_boxes),
        "names": NAMES,
        "weights": None,
    }


@app.get("/detections")
async def detections():
    """Return the current injected box list."""
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


def run() -> None:
    """CLI entry ``weed-spray-vision``."""
    uvicorn.run(
        "weed_spray.vision.main:app",
        host="127.0.0.1",
        port=8090,
        reload=False,
    )


if __name__ == "__main__":
    run()
