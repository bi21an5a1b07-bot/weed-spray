"""Frozen YOLO class map matches weeds.yaml; crabgrass is not a class."""

from pathlib import Path

from weed_spray.vision.classes import CLASSES, NAME_TO_ID, NAMES, NC, YAML_RELATIVE


def test_class_map_ids():
    assert NC == 4
    assert NAMES == {0: "dandelion", 1: "clover", 2: "thistle", 3: "mallow"}
    assert CLASSES == {"dandelion", "clover", "thistle", "mallow"}
    assert NAME_TO_ID["dandelion"] == 0
    assert NAME_TO_ID["thistle"] == 2
    assert NAME_TO_ID["mallow"] == 3


def test_yaml_matches_frozen_names():
    root = Path(__file__).resolve().parents[2]
    text = (root / YAML_RELATIVE).read_text()
    for idx, name in NAMES.items():
        assert name in text
        assert f"{idx}:" in text or f"{idx} :" in text
    assert "crabgrass" not in text
    assert "  background:" not in text
    assert "names:" in text
