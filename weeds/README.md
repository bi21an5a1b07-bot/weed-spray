# Weed detector data

Contract: `bot_files/weeds_class-map.md`, `weeds_notes.md`, `weeds_sources.md`.

Ids: `dandelion=0`, `clover=1`, `thistle=2`. Turf/crabgrass/other weeds are unlabeled background.

## Layout

```
weeds/
  weeds.yaml          # Ultralytics data file (frozen names)
  inbox/              # your backyard photos — domain val, do not mix into train by crop
  dataset/
    images/train/
    images/val/
    labels/train/     # YOLO txt, same stem as image
    labels/val/
```

## Rules

- One box per plant; whole plant; skip < ~20 px short side and blur.
- Split by image/source, never by cropping one photo into train and val.
- Hold `inbox/` as domain val.
- Do not download public archives until you approve a specific source (licenses: CC-BY-NC, ShareAlike, custom NC — see sources.md).

## Train (optional extra, RTX 4090)

```bash
uv sync --extra yolo
uv run weed-spray-train          # refuses if dataset is empty
uv run weed-spray-train --list-sources
```

SITL still passes with the **injector**. Live YOLO on RTSP is later, after weights exist.
