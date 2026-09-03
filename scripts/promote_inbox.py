"""Copy boxed inbox stills into weeds/dataset/{images,labels}/{train,val}/.

Split by image, never by cropping one photo. Does not train YOLO.

Default backyard clip: most frames → train; a held-out set → val
(thistle + dandelion + mallow + turf negatives). Same-clip frames still leak.

  uv run python scripts/promote_inbox.py
  uv run python scripts/promote_inbox.py --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "weeds" / "inbox"
DATASET = ROOT / "weeds" / "dataset"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Held-out val frames from the one backyard clip. Not a crop split.
BACKYARD_VAL_FRAMES = frozenset(
    {
        1,
        8,
        24,
        30,  # turf negatives
        7,
        21,
        22,  # thistle
        14,
        31,
        38,  # dandelion (38 = operator correction)
        50,
        55,
        59,  # mallow
        60,
        61,  # dandelion + mallow
    }
)


def frame_index(stem: str) -> int | None:
    """``frame_0007`` → 7. Other stems → None."""
    if not stem.startswith("frame_"):
        return None
    tail = stem.removeprefix("frame_")
    if tail.isdigit():
        return int(tail)
    return None


def assign_split(stem: str, source: str) -> str:
    """``train`` or ``val``. Backyard uses BACKYARD_VAL_FRAMES; other inbox → val."""
    if source == "backyard_weeds":
        idx = frame_index(stem)
        if idx is not None and idx in BACKYARD_VAL_FRAMES:
            return "val"
        return "train"
    return "val"


def dest_stem(source: str, image: Path) -> str:
    """Prefix so later sources do not collide (``backyard_weeds_frame_0007``)."""
    return f"{source}_{image.stem}"


def pair_label(image: Path) -> Path | None:
    """Sidecar ``.txt`` next to the jpg. Missing → skip (not yet boxed)."""
    txt = image.with_suffix(".txt")
    if txt.is_file():
        return txt
    return None


def list_pairs(folder: Path) -> list[tuple[Path, Path]]:
    """RGB files in ``folder`` that have a sidecar txt (empty txt is a negative)."""
    if not folder.is_dir():
        return []
    out: list[tuple[Path, Path]] = []
    for image in sorted(folder.iterdir()):
        if not image.is_file() or image.suffix.lower() not in IMAGE_EXTS:
            continue
        label = pair_label(image)
        if label is not None:
            out.append((image, label))
    return out


def copy_pair(
    image: Path,
    label: Path,
    split: str,
    stem: str,
    dataset: Path,
    *,
    force: bool,
) -> str:
    """Copy jpg + txt into ``dataset``. Returns ``copied`` / ``skip`` / ``error``."""
    img_dir = dataset / "images" / split
    lab_dir = dataset / "labels" / split
    img_dir.mkdir(parents=True, exist_ok=True)
    lab_dir.mkdir(parents=True, exist_ok=True)
    dest_img = img_dir / f"{stem}{image.suffix.lower()}"
    dest_lab = lab_dir / f"{stem}.txt"
    if dest_img.exists() and not force:
        return "skip"
    shutil.copy2(image, dest_img)
    shutil.copy2(label, dest_lab)
    return "copied"


def promote(
    inbox: Path = INBOX,
    dataset: Path = DATASET,
    source: str = "backyard_weeds",
    *,
    force: bool = False,
    dry_run: bool = False,
) -> int:
    """Promote one inbox folder. Return 2 if nothing to copy."""
    folder = inbox / source
    pairs = list_pairs(folder)
    if not pairs:
        print(f"no boxed stills in {folder}", file=sys.stderr)
        return 2
    counts = {"train": 0, "val": 0, "skip": 0}
    for image, label in pairs:
        split = assign_split(image.stem, source)
        stem = dest_stem(source, image)
        if dry_run:
            print(f"{split}\t{image.name} → {stem}")
            counts[split] += 1
            continue
        status = copy_pair(image, label, split, stem, dataset, force=force)
        if status == "skip":
            counts["skip"] += 1
        else:
            counts[split] += 1
    print(
        f"{source}: train={counts['train']} val={counts['val']} skip={counts['skip']}"
        + (" (dry-run)" if dry_run else "")
    )
    if dry_run:
        return 0
    if counts["train"] + counts["val"] == 0 and counts["skip"] == 0:
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI. Default source ``weeds/inbox/backyard_weeds/``."""
    parser = argparse.ArgumentParser(
        description="Copy boxed inbox stills into weeds/dataset/ (split by image)."
    )
    parser.add_argument("--source", default="backyard_weeds", help="inbox subfolder")
    parser.add_argument("--force", action="store_true", help="overwrite existing copies")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    return promote(source=args.source, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
