# Weed detector data

Contract: `bot_files/weeds_class-map.md`, `weeds_notes.md`, `weeds_sources.md`.

Ids: `dandelion=0`, `clover=1`, `thistle=2`, `mallow=3` (mallow includes ground ivy). Turf/crabgrass/plantain/spurge are unlabeled background.

## Layout

```
weeds/
  weeds.yaml          # Ultralytics data file (frozen names)
  inbox/              # unlabeled intake — domain val, do not mix into train by crop
    dandelion/ clover/ thistle/   # iNat CC0/CC-BY (SOURCES.csv)
    backyard_weeds/               # 1 fps stills from media/backyard_weeds.MOV
  dataset/
    images/train/
    images/val/
    labels/train/     # YOLO txt, same stem as image
    labels/val/
```

`inbox/` and labeled `dataset/` images are gitignored. The trees stay.

## Inbox now

| Folder | What | Count |
|---|---|---|
| `inbox/dandelion` `clover` `thistle` | iNat research-grade CC0/CC-BY | 25 each (`SOURCES.csv`) |
| `inbox/backyard_weeds` | Operator lawn clip, 1 fps JPEG | 61 (`frame_0001.jpg` … `frame_0061.jpg`) |

Re-extract the clip (skips if frames exist):

```bash
uv run python scripts/extract_clip_inbox.py
# --force to replace stills; --dry-run to print ffmpeg only
```

Do **not** copy inbox files into `dataset/` until they are boxed. No train/val split by cropping one frame.

## Boxing (human)

Rules: `bot_files/weeds_notes.md`. One box per plant; whole plant; skip &lt; ~20 px short side and blur.

Write YOLO txt **next to** the jpg (same stem):

```
# frame_0061.txt
0 0.72 0.48 0.12 0.22
```

`class x_center y_center width height` in 0–1 of image size. Classes: `0` dandelion, `1` clover, `2` thistle, `3` mallow.

This backyard clip is close-range handheld over turf. Dandelion clocks/rosettes and mallow/ground ivy are labeled. Spotted spurge (ferny mats) and plantain stay unlabeled. Do not label clover unless it is clearly *Trifolium*. Skip turf-only or smeared frames.

A local **draft** of sidecar txt is in `inbox/backyard_weeds/` (`DRAFT.md`). Estimated boxes; not a spray confirm. Overlay previews (gitignored): `var/label-draft-preview/`.

Hold boxed backyard stills as **domain val**. iNat close-ups are a different GSD — do not hide that by splitting one photo across train and val.

Promote boxed stills (split by image, not by crop):

```bash
uv run python scripts/promote_inbox.py          # skip existing copies
uv run python scripts/promote_inbox.py --force  # replace
uv run python scripts/promote_inbox.py --dry-run
```

Backyard val hold-outs are listed in `dataset/SPLIT.md`. Inbox originals stay put.

## Train (optional extra, RTX 4090)

```bash
uv sync --extra yolo
uv run weed-spray-train          # refuses if dataset is empty
uv run weed-spray-train --list-sources
```

SITL still passes with the **injector**. Live YOLO on RTSP is later, after weights exist.
