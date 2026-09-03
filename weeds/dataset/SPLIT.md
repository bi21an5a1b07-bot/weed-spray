# Dataset split

Copied from boxed `weeds/inbox/` by `scripts/promote_inbox.py`. Split **by image**, never by cropping one photo into train and val.

## backyard_weeds (this clip)

Same 61 s handheld clip. Adjacent 1 fps frames leak. Val is a hold-out, not a different lawn.

| Split | Rule |
|---|---|
| **val** | Frames `0001 0007 0008 0014 0021 0022 0024 0030 0031 0038 0050 0055 0059 0060 0061` — turf negatives, thistle, dandelion (incl. operator `0038`), mallow, mixed |
| **train** | Remaining boxed frames from this folder |

Names: `backyard_weeds_frame_XXXX.{jpg,txt}`. Empty txt = negative (turf).

iNat inbox photos are not promoted (no boxes). Do not hide bloom-only iNat in train later without a val slice.

Re-copy:

```bash
uv run python scripts/promote_inbox.py --force
```

Train is a later step: `uv sync --extra yolo && uv run weed-spray-train`.
