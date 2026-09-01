"""Train YOLO on weeds/weeds.yaml. Does not download public archives."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from weed_spray.vision.classes import CLASSES, NAMES, NC, YAML_RELATIVE

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def repo_root() -> Path:
    """Directory that contains ``weeds/weeds.yaml`` (cwd or parents of this file)."""
    cwd = Path.cwd()
    if (cwd / YAML_RELATIVE).is_file():
        return cwd
    for parent in Path(__file__).resolve().parents:
        if (parent / YAML_RELATIVE).is_file():
            return parent
    return cwd


ROOT = repo_root()
YAML = ROOT / YAML_RELATIVE


def _count_images(split: str) -> int:
    """Count RGB files in ``weeds/dataset/images/{train,val}``. Ignores .gitkeep."""
    folder = ROOT / "weeds" / "dataset" / "images" / split
    if not folder.is_dir():
        return 0
    return sum(1 for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def list_sources() -> None:
    """Print the Bot source table. Does not download archives."""
    src = ROOT / "bot_files" / "weeds_sources.md"
    print(src.read_text() if src.is_file() else "missing bot_files/weeds_sources.md")
    print("\nDo not download until you pick a license-clear source and say so.")
    print("Priority collect: your own lawn photos in weeds/inbox/ (1-10 m and 6-12 in AGL).")


def train(device: str, epochs: int, imgsz: int, model: str) -> int:
    """Run Ultralytics on ``weeds.yaml``. Exit 2 if dataset empty or extra missing."""
    n_train = _count_images("train")
    n_val = _count_images("val")
    if n_train < 1 or n_val < 1:
        print(
            f"dataset empty (train={n_train} val={n_val}). "
            "Label images into weeds/dataset/ or put backyard photos in weeds/inbox/. "
            "Public dumps are not fetched automatically (bot_files/weeds_sources.md).",
            file=sys.stderr,
        )
        return 2
    try:
        from ultralytics import YOLO
    except ImportError:
        print("install the extra: uv sync --extra yolo", file=sys.stderr)
        return 2
    print(f"classes={NAMES} nc={NC} train={n_train} val={n_val}")
    YOLO(model).train(
        data=str(YAML),
        epochs=epochs,
        imgsz=imgsz,
        device=device,
        project=str(ROOT / "var" / "yolo"),
        name="weeds",
        exist_ok=True,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI ``weed-spray-train``. ``--list-sources`` never fetches data."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-sources", action="store_true")
    parser.add_argument("--device", default="0")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--model", default="yolov8n.pt")
    args = parser.parse_args(argv)
    if args.list_sources:
        list_sources()
        return 0
    if not YAML.is_file():
        print(f"missing {YAML}", file=sys.stderr)
        return 2
    text = YAML.read_text()
    for name in CLASSES:
        if name not in text:
            print(f"weeds.yaml missing class {name}", file=sys.stderr)
            return 2
    return train(args.device, args.epochs, args.imgsz, args.model)


if __name__ == "__main__":
    sys.exit(main())
