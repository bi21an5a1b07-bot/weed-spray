"""Vision injector HTTP: frozen names, upsert, delete, 422 on unknown class."""

import logging

from fastapi.testclient import TestClient

from weed_spray.vision import runtime
from weed_spray.vision.main import app


def test_health_names(monkeypatch):
    monkeypatch.delenv("WEED_YOLO_WEIGHTS", raising=False)
    with TestClient(app) as client:
        body = client.get("/health").json()
        assert body["ok"] is True
        assert body["mode"] == "injector"
        assert body["weights"] is None
        assert body["names"]["0"] == "dandelion"
        assert body["names"]["2"] == "thistle"
        assert body["names"]["3"] == "mallow"


def test_configure_logging_prints_missing_weights(monkeypatch, tmp_path, capsys):
    missing = tmp_path / "no-such.pt"
    monkeypatch.setenv("WEED_YOLO_WEIGHTS", str(missing))
    runtime.reset_for_tests()
    runtime.configure_logging()
    runtime.note_configured_weights()
    err = capsys.readouterr().err
    assert f"WEED_YOLO_WEIGHTS {missing} is missing; staying injector" in err


def test_yolo_mode_serves_pixels_not_metres(monkeypatch, tmp_path):
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"not-a-model")
    monkeypatch.setenv("WEED_YOLO_WEIGHTS", str(weights))
    runtime.reset_for_tests()
    runtime.attach_reader(
        weights=str(weights),
        rows=[
            {
                "class": "dandelion",
                "conf": 0.9,
                "cx": 0.5,
                "cy": 0.4,
                "w": 0.2,
                "h": 0.2,
                "frame_w": 640,
                "frame_h": 480,
                "frame_t": "t0",
            }
        ],
        camera_ok=True,
    )
    with TestClient(app) as client:
        health = client.get("/health").json()
        listed = client.get("/detections").json()["detections"]
    assert health["mode"] == "yolo"
    assert health["weights"] == str(weights)
    assert health["camera"] is True
    assert listed[0]["class"] == "dandelion"
    assert "north_m" not in listed[0]
    assert runtime.runner_started() is True


def test_yolo_camera_down_returns_no_boxes(monkeypatch, tmp_path):
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"not-a-model")
    monkeypatch.setenv("WEED_YOLO_WEIGHTS", str(weights))
    runtime.reset_for_tests()
    runtime.attach_reader(weights=str(weights), rows=[], camera_ok=False)
    with TestClient(app) as client:
        health = client.get("/health").json()
        listed = client.get("/detections").json()["detections"]
    assert health["ok"] is True
    assert health["mode"] == "yolo"
    assert health["camera"] is False
    assert listed == []


def test_missing_weights_stay_injector_and_do_not_start_runner(monkeypatch, tmp_path, caplog):
    missing = tmp_path / "no-such.pt"
    monkeypatch.setenv("WEED_YOLO_WEIGHTS", str(missing))
    runtime.reset_for_tests()
    with caplog.at_level(logging.INFO, logger="weed_spray.vision"):
        with TestClient(app) as client:
            first = client.get("/health").json()
            second = client.get("/health").json()
    assert first["ok"] is True
    assert first["mode"] == "injector"
    assert first["weights"] is None
    assert second["mode"] == "injector"
    assert runtime.runner_started() is False
    notes = [rec.getMessage() for rec in caplog.records if "missing" in rec.getMessage()]
    assert notes == [f"WEED_YOLO_WEIGHTS {missing} is missing; staying injector"]


def test_inject_get_delete_and_reject_crabgrass():
    with TestClient(app) as client:
        bad = client.post(
            "/inject",
            json={"detections": [{"id": "x", "class": "crabgrass", "north_m": 0, "east_m": 0}]},
        )
        assert bad.status_code == 422

        ok = client.post(
            "/inject",
            json={
                "detections": [
                    {
                        "id": "w1",
                        "class": "dandelion",
                        "north_m": 1,
                        "east_m": 2,
                        "conf": 0.8,
                    }
                ]
            },
        )
        assert ok.status_code == 200
        assert ok.json()["detections"][0]["class"] == "dandelion"

        listed = client.get("/detections").json()["detections"]
        assert len(listed) == 1
        assert listed[0]["id"] == "w1"

        client.post(
            "/inject",
            json={"detections": [{"id": "w1", "class": "clover", "north_m": 3, "east_m": 4}]},
        )
        listed = client.get("/detections").json()["detections"]
        assert len(listed) == 1
        assert listed[0]["class"] == "clover"

        mallow = client.post(
            "/inject",
            json={"detections": [{"id": "m1", "class": "mallow", "north_m": 5, "east_m": 6}]},
        )
        assert mallow.status_code == 200
        assert mallow.json()["detections"][-1]["class"] == "mallow"

        client.delete("/detections")
        assert client.get("/detections").json()["detections"] == []
