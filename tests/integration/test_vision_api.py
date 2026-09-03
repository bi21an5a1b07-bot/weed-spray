"""Vision injector HTTP: frozen names, upsert, delete, 422 on unknown class."""

from fastapi.testclient import TestClient

from weed_spray.vision.main import app


def test_health_names():
    with TestClient(app) as client:
        body = client.get("/health").json()
        assert body["ok"] is True
        assert body["mode"] == "injector"
        assert body["names"]["0"] == "dandelion"
        assert body["names"]["2"] == "thistle"
        assert body["names"]["3"] == "mallow"


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
