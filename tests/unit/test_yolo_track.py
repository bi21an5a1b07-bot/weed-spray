"""Scan-time YOLO tracks. FakeVehicle only. Inject is not confirm."""

import math

import pytest

from tests.fakes import FakeVehicle
from weed_spray.backend.config import Settings
from weed_spray.backend.mission import Mission
from weed_spray.backend.models import ConfirmEvent, FenceBox, InjectRequest, MissionPhase
from weed_spray.backend.models import Detection as Det


def _settings(**kwargs) -> Settings:
    base = dict(
        yolo_georeference=True,
        cam_hfov_deg=90.0,
        cam_tilt_deg=90.0,
        yolo_assoc_m=0.35,
        yolo_conf=0.5,
        yolo_imgsz=640,
    )
    base.update(kwargs)
    return Settings(**base)


def _pixel(**kwargs) -> dict:
    row = {
        "class": "dandelion",
        "conf": 0.9,
        "cx": 0.5,
        "cy": 0.5,
        "w": 0.2,
        "h": 0.2,
        "frame_w": 640,
        "frame_h": 480,
    }
    row.update(kwargs)
    return row


def _mission(monkeypatch, **setting_overrides) -> Mission:
    monkeypatch.setattr(
        "weed_spray.backend.mission.settings",
        _settings(**setting_overrides),
    )
    vehicle = FakeVehicle()
    vehicle.connected = True
    vehicle._telem.north_m = 10.0
    vehicle._telem.east_m = 4.0
    vehicle._telem.heading_deg = 0.0
    vehicle._telem.distance_scan_m = 2.0
    vehicle._telem.distance_sensor_stream_alive = True
    mission = Mission(vehicle)
    mission.state.phase = MissionPhase.scanning
    mission.state.fence = FenceBox(north_m=20, south_m=-5, east_m=15, west_m=-15)
    return mission


def test_unset_tilt_does_not_place_a_plant(monkeypatch):
    mission = _mission(monkeypatch, cam_tilt_deg=None)
    mission.observe_pixels([_pixel()])
    assert mission.state.detections == []
    assert "tilt" in (mission.state.last_error or "")


def test_forward_tilt_stores_the_ground_point_ahead(monkeypatch):
    mission = _mission(monkeypatch, cam_tilt_deg=15.0)
    mission.observe_pixels([_pixel()])
    det = mission.state.detections[0]
    assert det.confirmed is False
    assert det.id == "y1"
    # 2 m scan height / tan(15°) forward of the vehicle at north 10, heading 0.
    assert det.north_m == pytest.approx(10.0 + 2.0 / math.tan(math.radians(15.0)))
    assert det.east_m == pytest.approx(4.0)


def test_flag_off_does_not_copy_pixels(monkeypatch):
    mission = _mission(monkeypatch, yolo_georeference=False)
    mission.observe_pixels([_pixel()])
    assert mission.state.detections == []


def test_two_close_hits_share_id_and_median(monkeypatch):
    mission = _mission(monkeypatch)
    mission.observe_pixels([_pixel()])
    mission.observe_pixels([_pixel(cx=0.5 + 32 / 640)])
    assert [d.id for d in mission.state.detections] == ["y1"]
    det = mission.state.detections[0]
    assert det.class_name == "dandelion"
    assert det.confirmed is False
    assert det.north_m == pytest.approx(10.0)
    assert det.east_m == pytest.approx(4.1)


def test_different_class_nearby_is_a_second_id(monkeypatch):
    mission = _mission(monkeypatch)
    mission.observe_pixels([_pixel(), _pixel(**{"class": "clover"})])
    assert [d.id for d in mission.state.detections] == ["y1", "y2"]
    assert {d.class_name for d in mission.state.detections} == {"dandelion", "clover"}


def test_same_class_beyond_assoc_is_a_second_id(monkeypatch):
    mission = _mission(monkeypatch)
    mission.observe_pixels([_pixel()])
    mission.observe_pixels([_pixel(cx=0.5 + 80 / 640)])
    assert [d.id for d in mission.state.detections] == ["y1", "y2"]
    assert mission.state.detections[1].east_m == pytest.approx(4.5)


def test_confirm_freezes_position(monkeypatch):
    mission = _mission(monkeypatch)
    mission.observe_pixels([_pixel()])
    mission.state.detections[0].confirmed = True
    mission.state.confirms.append(ConfirmEvent(detection_id="y1", decision="confirm"))
    mission.state.phase = MissionPhase.scanning
    mission.observe_pixels([_pixel(cx=0.5 + 32 / 640)])
    det = mission.state.detections[0]
    assert det.confirmed is True
    assert det.north_m == pytest.approx(10.0)
    assert det.east_m == pytest.approx(4.0)


def test_reject_stays_rejected(monkeypatch):
    mission = _mission(monkeypatch)
    mission.observe_pixels([_pixel()])
    mission.state.confirms.append(ConfirmEvent(detection_id="y1", decision="reject"))
    mission.state.phase = MissionPhase.scanning
    mission.observe_pixels([_pixel(cx=0.5 + 32 / 640)])
    det = mission.state.detections[0]
    assert det.confirmed is False
    assert det.east_m == pytest.approx(4.0)


def test_not_scanning_adds_nothing(monkeypatch):
    mission = _mission(monkeypatch)
    mission.state.phase = MissionPhase.awaiting_confirm
    mission.observe_pixels([_pixel()])
    assert mission.state.detections == []


def test_low_conf_and_tiny_box_and_outside_fence_are_ignored(monkeypatch):
    mission = _mission(monkeypatch)
    mission.vehicle._telem.east_m = 14.95
    mission.observe_pixels(
        [
            _pixel(conf=0.49),
            _pixel(h=19 / 640),
            _pixel(cx=0.5 + 32 / 640),
        ]
    )
    assert mission.state.detections == []


def test_missing_lidar_or_hfov_skips_without_using_baro(monkeypatch):
    mission = _mission(monkeypatch, cam_hfov_deg=None)
    mission.vehicle._telem.distance_scan_m = None
    mission.vehicle._telem.relative_alt_m = 2.0
    mission.vehicle._telem.ned_down_m = 2.0
    mission.observe_pixels([_pixel()])
    assert mission.state.detections == []
    assert mission.state.last_error
    assert "relative" not in mission.state.last_error
    assert "lidar" in mission.state.last_error

    mission = _mission(monkeypatch, cam_hfov_deg=None)
    mission.observe_pixels([_pixel()])
    assert mission.state.detections == []
    assert "HFOV" in (mission.state.last_error or "")


def test_sticky_scan_without_stream_alive_skips(monkeypatch):
    """Stale distance_scan_m must not unlock georef when the stream is dead."""
    mission = _mission(monkeypatch)
    mission.vehicle._telem.distance_scan_m = 2.0
    mission.vehicle._telem.distance_sensor_stream_alive = False
    mission.observe_pixels([_pixel()])
    assert mission.state.detections == []
    assert "lidar" in (mission.state.last_error or "")


def test_inject_w1_stays_beside_y1(monkeypatch):
    mission = _mission(monkeypatch)
    mission.inject(
        InjectRequest(
            detections=[Det(id="w1", class_name="thistle", north_m=1.0, east_m=2.0, conf=1.0)]
        )
    )
    mission.state.phase = MissionPhase.scanning
    mission.observe_pixels([_pixel()])
    assert [d.id for d in mission.state.detections] == ["w1", "y1"]
    assert mission.state.detections[1].confirmed is False


@pytest.mark.asyncio
async def test_vision_down_does_not_fail_the_scan(monkeypatch, caplog):
    mission = _mission(monkeypatch)

    async def boom():
        raise ConnectionError("vision down")

    mission._fetch_yolo_pixels = boom
    with caplog.at_level("WARNING"):
        await mission._run_inner()
    assert mission.state.phase == MissionPhase.awaiting_confirm
    assert mission._yolo_task is not None
    assert mission._yolo_task.done()
    assert any("vision down" in rec.getMessage() for rec in caplog.records)


def test_stamp_yolo_ids_attaches_mission_id(monkeypatch):
    """Overlay click needs the y* id on the pixel row after observe_pixels."""
    mission = _mission(monkeypatch)
    mission.observe_pixels([_pixel()])
    assert [d.id for d in mission.state.detections] == ["y1"]
    stamped = mission.stamp_yolo_ids([_pixel()])
    assert stamped[0]["id"] == "y1"
    assert stamped[0]["cx"] == pytest.approx(0.5)


def test_stamp_yolo_ids_skips_when_georef_off(monkeypatch):
    mission = _mission(monkeypatch, yolo_georeference=False)
    mission.state.detections = [
        Det(id="y1", class_name="dandelion", north_m=10.0, east_m=4.0, conf=0.9)
    ]
    stamped = mission.stamp_yolo_ids([_pixel()])
    assert "id" not in stamped[0]
