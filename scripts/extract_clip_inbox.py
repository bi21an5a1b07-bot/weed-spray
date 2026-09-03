"""Extract unlabeled stills from a lawn clip into weeds/inbox/<stem>/.

Does not box, does not split train/val, does not train YOLO.

  uv run python scripts/extract_clip_inbox.py
  uv run python scripts/extract_clip_inbox.py --clip media/backyard_weeds.MOV
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media"
INBOX = ROOT / "weeds" / "inbox"
DATASET = ROOT / "weeds" / "dataset"

DEFAULT_FPS = 1.0
DEFAULT_QUALITY = 2
DEFAULT_CLIP_NAMES = (
    "backyard_weeds.MOV",
    "backyard_weeds.mov",
    "backyard_weeds.mp4",
)

Runner = Callable[[Sequence[str]], int]


def default_clip(media: Path = MEDIA) -> Path | None:
    """First existing default clip name under ``media/`` (MOV before mp4)."""
    for name in DEFAULT_CLIP_NAMES:
        path = media / name
        if path.is_file():
            return path
    return None


def inbox_dest(clip: Path, inbox: Path = INBOX) -> Path:
    """``weeds/inbox/<clip-stem>/``. Stem keeps mixed-case files in one folder."""
    return inbox / clip.stem.lower()


def dest_error(dest: Path, inbox: Path = INBOX, dataset: Path = DATASET) -> str | None:
    """Reject writes outside inbox or into the labeled dataset tree."""
    dest_r = dest.resolve()
    inbox_r = inbox.resolve()
    dataset_r = dataset.resolve()
    try:
        dest_r.relative_to(inbox_r)
    except ValueError:
        return f"dest {dest} is not under {inbox}"
    if dest_r == inbox_r:
        return f"dest must be a subfolder of {inbox}"
    try:
        dest_r.relative_to(dataset_r)
    except ValueError:
        return None
    return f"dest {dest} is under {dataset} — inbox only, no train/val split"


def existing_frames(dest: Path) -> list[Path]:
    """JPEG stills named ``frame_*`` in ``dest``."""
    if not dest.is_dir():
        return []
    return sorted(
        p
        for p in dest.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"} and p.stem.startswith("frame_")
    )


def ffmpeg_argv(clip: Path, dest: Path, fps: float, quality: int) -> list[str]:
    """1 fps (default) JPEG dump. Video only. ``frame_%04d.jpg``."""
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(clip),
        "-map",
        "0:v:0",
        "-vf",
        f"fps={fps}",
        "-q:v",
        str(quality),
        "-an",
        str(dest / "frame_%04d.jpg"),
    ]


def source_markdown(clip: Path, dest: Path, fps: float, quality: int, count: int) -> str:
    """Provenance for boxing. Not a class label."""
    rel_clip = clip
    rel_dest = dest
    try:
        rel_clip = clip.resolve().relative_to(ROOT)
    except ValueError:
        pass
    try:
        rel_dest = dest.resolve().relative_to(ROOT)
    except ValueError:
        pass
    return (
        f"# Unlabeled intake: {dest.name}\n\n"
        f"Source clip: `{rel_clip}`\n"
        f"Extract: {fps:g} fps JPEG (`frame_%04d.jpg`), ffmpeg `-q:v {quality}`\n"
        f"Count: {count} files in `{rel_dest}`\n\n"
        "Role: operator lawn stills. Hold as **domain val** after boxing "
        "(`bot_files/weeds_class-map.md`). Do not crop one frame into train and val.\n\n"
        "When boxing (`bot_files/weeds_notes.md`):\n"
        "- `0` dandelion (rosette, yellow bloom, or clock — one box per plant)\n"
        "- `1` clover (*Trifolium* only; not wood sorrel)\n"
        "- `2` thistle\n"
        "- `3` mallow (includes ground ivy; not spotted spurge)\n\n"
        "Turf, crabgrass, plantain, and anything unsure stay unlabeled background.\n"
        "Skip blur, plants cut so species is a guess, and boxes shorter than ~20 px.\n\n"
        "Write YOLO txt next to each jpg (`frame_0061.txt`). "
        "Do not copy into `weeds/dataset/` until a later promote step.\n"
    )


def write_source_md(dest: Path, clip: Path, fps: float, quality: int, count: int) -> Path:
    """Write ``SOURCE.md`` beside the frames (gitignored under inbox)."""
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / "SOURCE.md"
    path.write_text(source_markdown(clip, dest, fps, quality, count), encoding="utf-8")
    return path


def run_ffmpeg(argv: Sequence[str]) -> int:
    """Host ffmpeg. Returns the process exit code; missing binary is 2."""
    if shutil.which(argv[0]) is None:
        print("ffmpeg not on PATH (apt install ffmpeg)", file=sys.stderr)
        return 2
    completed = subprocess.run(argv, check=False)
    return int(completed.returncode)


def extract(
    clip: Path,
    dest: Path,
    fps: float = DEFAULT_FPS,
    quality: int = DEFAULT_QUALITY,
    *,
    force: bool = False,
    dry_run: bool = False,
    runner: Runner = run_ffmpeg,
    inbox: Path = INBOX,
    dataset: Path = DATASET,
) -> int:
    """Dump stills unless they already exist. Always refresh ``SOURCE.md`` when count > 0."""
    err = dest_error(dest, inbox=inbox, dataset=dataset)
    if err:
        print(err, file=sys.stderr)
        return 2
    if fps <= 0:
        print("fps must be > 0", file=sys.stderr)
        return 2
    if quality < 1 or quality > 31:
        print("quality must be ffmpeg -q:v in 1..31 (lower is better)", file=sys.stderr)
        return 2
    if not clip.is_file():
        print(f"missing clip {clip}", file=sys.stderr)
        return 2

    present = existing_frames(dest)
    argv = ffmpeg_argv(clip, dest, fps, quality)
    if dry_run:
        print(" ".join(argv))
        print(f"dest {dest} existing={len(present)} force={force}")
        return 0

    if present and not force:
        write_source_md(dest, clip, fps, quality, len(present))
        print(f"skip extract ({len(present)} frames already in {dest}); wrote SOURCE.md")
        return 0

    dest.mkdir(parents=True, exist_ok=True)
    if force:
        for old in existing_frames(dest):
            old.unlink()
    code = runner(argv)
    if code != 0:
        print(f"ffmpeg exited {code}", file=sys.stderr)
        return 2
    count = len(existing_frames(dest))
    write_source_md(dest, clip, fps, quality, count)
    print(f"wrote {count} frames + {dest / 'SOURCE.md'}")
    return 0 if count else 2


def main(argv: list[str] | None = None) -> int:
    """CLI. Default clip is ``media/backyard_weeds.MOV`` (or .mov / .mp4)."""
    parser = argparse.ArgumentParser(
        description="Extract unlabeled 1 fps JPEGs into weeds/inbox/<stem>/."
    )
    parser.add_argument("--clip", type=Path, default=None, help="source video")
    parser.add_argument("--dest", type=Path, default=None, help="inbox subfolder")
    parser.add_argument("--fps", type=float, default=DEFAULT_FPS)
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY, help="ffmpeg -q:v")
    parser.add_argument("--force", action="store_true", help="replace existing frame_*.jpg")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    clip = args.clip if args.clip is not None else default_clip()
    if clip is None:
        print(
            "no clip: pass --clip or put backyard_weeds.MOV in media/",
            file=sys.stderr,
        )
        return 2
    dest = args.dest if args.dest is not None else inbox_dest(clip)
    return extract(
        clip,
        dest,
        fps=args.fps,
        quality=args.quality,
        force=args.force,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
