"""Compare bot_files/ to a sha256 snapshot.

Exit 0 if there is nothing to process (including first-run baseline).
Exit 1 if files were added, changed, or removed.

  uv run python scripts/bot_files_delta.py
  uv run python scripts/bot_files_delta.py --commit
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOT_FILES = ROOT / "bot_files"
STATE_PATH = ROOT / "var" / "bot_files-state.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(folder: Path) -> dict[str, str]:
    """Map filename → sha256 for regular files in ``folder`` (not recursive)."""
    out: dict[str, str] = {}
    if not folder.is_dir():
        return out
    for path in sorted(folder.iterdir()):
        if path.is_file() and not path.name.startswith("."):
            out[path.name] = _sha256(path)
    return out


def diff(old: dict[str, str], new: dict[str, str]) -> dict[str, list[str]]:
    """Return added / changed / removed names."""
    old_names, new_names = set(old), set(new)
    return {
        "added": sorted(new_names - old_names),
        "changed": sorted(name for name in (old_names & new_names) if old[name] != new[name]),
        "removed": sorted(old_names - new_names),
    }


def load_state(path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    raw = json.loads(path.read_text())
    files = raw.get("files", raw)
    return {str(k): str(v) for k, v in files.items()}


def save_state(path: Path, files: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"files": files}, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=BOT_FILES)
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Write the current snapshot (after processing a delta).",
    )
    args = parser.parse_args(argv)
    current = snapshot(args.dir)
    previous = load_state(args.state)

    if args.commit or previous is None:
        save_state(args.state, current)
        payload = {
            "baseline": previous is None and not args.commit,
            "committed": True,
            "count": len(current),
            **diff(previous or {}, current),
        }
        print(json.dumps(payload, indent=2))
        return 0

    delta = diff(previous, current)
    pending = bool(delta["added"] or delta["changed"] or delta["removed"])
    payload = {"baseline": False, "committed": False, "count": len(current), **delta}
    print(json.dumps(payload, indent=2))
    return 1 if pending else 0


if __name__ == "__main__":
    sys.exit(main())
