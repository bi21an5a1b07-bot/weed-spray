# Vision

Contract: `bot_files/weeds_class-map.md`, `weeds_notes.md`, `weeds_sources.md`.

## Frozen classes

| id | name | Notes |
|---:|---|---|
| 0 | `dandelion` | *Taraxacum*. Not crabgrass, not cat’s-ear if unsure |
| 1 | `clover` | *Trifolium*. Not *Oxalis* |
| 2 | `thistle` | *Cirsium* / *Carduus* as one class |
| 3 | `mallow` | *Malva* + ground ivy (*Glechoma*) as one class. Not spotted spurge |

`nc: 4`. Never renumber 0/1/2. Turf, dirt, crabgrass, plantain, “other_weed” are **unlabeled background**.

Code source of truth: `weeds/weeds.yaml` and `weed_spray.vision.classes`.

## SITL v1

The vision worker is an **injector** until `WEED_YOLO_WEIGHTS` points at a real file. A missing path stays the injector. A present file serves pixel rows on `GET /detections` (no north/east). Without the `yolo` extra the process stays up and reports `camera: false`.

```bash
uv sync --extra yolo
WEED_YOLO_WEIGHTS=var/yolo/weeds/weights/best.pt uv run weed-spray-vision
```

The Gazebo scan camera looks forward and 15° down. The backend copies pixels into the mission only when `WEED_YOLO_GEOREFERENCE=1` during a Gazebo (or hardware) scan, with live scan-height lidar, `WEED_CAM_TILT_DEG`, and `WEED_CAM_HFOV_DEG`. The sourced Gazebo lens is 99.7° (1.74 rad), not the unit-test 90°. The stored point is the ground hit ahead of the aircraft. Hover descent waits until the vehicle is within 0.5 m of that point. Do not turn georeference on for SIH. How to check each mode: [acceptance.md](acceptance.md#vision-and-georeference).

`weed-spray-train` refuses an empty `weeds/dataset/`, and it refuses when any of the four classes has zero label rows paired to an image in train. An orphan label file does not count. Clover may be absent from the backyard clip; do not describe that class as detected.

## Training (optional)

```bash
uv sync --extra yolo
uv run weed-spray-train --list-sources   # prints bot_files/weeds_sources.md
uv run weed-spray-train                  # needs images in weeds/dataset/images/{train,val}
```

Public archives are **not** auto-downloaded (licenses: CC-BY-NC, ShareAlike, custom NC; no 3-class US-lawn set). Operator-approved iNat CC0/CC-BY stills sit in `weeds/inbox/{dandelion,clover,thistle}/`. Highest-value data: operator lawn stills in `weeds/inbox/backyard_weeds/` (1 fps from `media/backyard_weeds.MOV`).

```bash
uv run python scripts/extract_clip_inbox.py   # skip if frames exist; --force to replace
```

Labeling: one box per plant; whole plant; skip boxes &lt; ~20 px short side; split by image, never by cropping one photo into train and val. Promote: `uv run python scripts/promote_inbox.py` (see `weeds/dataset/SPLIT.md`). Hold a backyard val slice; do not crop one frame into both splits. See `weeds/README.md`.
