"""Pydantic aliases (JSON ``class``) and confirm / pump-off shapes."""

import pytest
from pydantic import ValidationError

from weed_spray.backend.models import ConfirmRequest, Detection, InjectRequest, PumpOffEvent


def test_detection_alias_class():
    d = Detection.model_validate({"id": "w1", "class": "dandelion", "north_m": 1.0, "east_m": 2.0})
    assert d.class_name == "dandelion"
    dumped = d.model_dump(by_alias=True)
    assert dumped["class"] == "dandelion"


def test_confirm_ids_and_decisions():
    req = ConfirmRequest(
        ids=["a"],
        decisions=[{"detection_id": "b", "decision": "reject"}],
    )
    assert req.ids == ["a"]
    assert req.decisions[0].decision == "reject"


def test_inject_roundtrip():
    req = InjectRequest.model_validate(
        {"detections": [{"id": "w1", "class": "clover", "north_m": 0, "east_m": 1, "conf": 0.9}]}
    )
    assert req.detections[0].class_name == "clover"


def test_pump_off_kill_ok():
    PumpOffEvent(type="kill", pump_commanded_off=True)


def test_pump_off_rejects_unknown_type():
    with pytest.raises(ValidationError):
        PumpOffEvent(type="explode", pump_commanded_off=True)
