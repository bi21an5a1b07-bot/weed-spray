"""bot_files snapshot: baseline, added/changed/removed, commit."""

from pathlib import Path

from scripts.bot_files_delta import diff, main, snapshot


def test_snapshot_skips_dotfiles(tmp_path: Path):
    (tmp_path / "keep.md").write_text("a\n")
    (tmp_path / ".hidden").write_text("no\n")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.md").write_text("no\n")
    names = snapshot(tmp_path)
    assert set(names) == {"keep.md"}


def test_diff_added_changed_removed():
    old = {"a.md": "1", "b.md": "2"}
    new = {"b.md": "9", "c.md": "3"}
    assert diff(old, new) == {
        "added": ["c.md"],
        "changed": ["b.md"],
        "removed": ["a.md"],
    }


def test_main_baseline_then_delta(tmp_path: Path, capsys):
    folder = tmp_path / "bot"
    state = tmp_path / "state.json"
    folder.mkdir()
    (folder / "loop.md").write_text("one\n")
    assert main(["--dir", str(folder), "--state", str(state)]) == 0
    out = capsys.readouterr().out
    assert '"baseline": true' in out

    assert main(["--dir", str(folder), "--state", str(state)]) == 0
    assert '"added": []' in capsys.readouterr().out

    (folder / "loop.md").write_text("two\n")
    (folder / "faa_current.md").write_text("new\n")
    assert main(["--dir", str(folder), "--state", str(state)]) == 1
    delta = capsys.readouterr().out
    assert "loop.md" in delta
    assert "faa_current.md" in delta

    assert main(["--dir", str(folder), "--state", str(state), "--commit"]) == 0
    assert main(["--dir", str(folder), "--state", str(state)]) == 0
