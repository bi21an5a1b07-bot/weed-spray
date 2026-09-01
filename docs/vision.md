# Vision

Contract: `bot_files/weeds_class-map.md`, `weeds_notes.md`, `weeds_sources.md`.

## Frozen classes

| id | name | Notes |
|---:|---|---|
| 0 | `dandelion` | *Taraxacum*. Not crabgrass, not cat’s-ear if unsure |
| 1 | `clover` | *Trifolium*. Not *Oxalis* |
| 2 | `thistle` | *Cirsium* / *Carduus* as one class |

`nc: 3`. Never renumber. Turf, dirt, crabgrass, “other_weed” are **unlabeled background**, not a fourth class.

Code source of truth: `weeds/weeds.yaml` and `weed_spray.vision.classes`.

## SITL v1

The vision worker is an **injector**. Live YOLO on RTSP is later, after labeled data exists. `weed-spray-train` refuses to run on an empty `weeds/dataset/`.

## Training (optional)

```bash
uv sync --extra yolo
uv run weed-spray-train --list-sources   # prints bot_files/weeds_sources.md
uv run weed-spray-train                  # needs images in weeds/dataset/images/{train,val}
```

Public archives are **not** downloaded (licenses: CC-BY-NC, ShareAlike, custom NC; no 3-class US-lawn set). Highest-value data: operator photos in `weeds/inbox/` at 1–10 m and 6–12 in AGL.

Labeling: one box per plant; whole plant; skip boxes &lt; ~20 px short side; split by image, never by cropping one photo into train and val.
