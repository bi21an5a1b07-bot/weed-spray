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

The vision worker is an **injector**. Live YOLO on RTSP is later, after labeled data exists. `weed-spray-train` refuses to run on an empty `weeds/dataset/`.

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
