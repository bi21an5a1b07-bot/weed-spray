"""extract_clip_inbox: dest guards, skip-if-present, no dataset writes."""

from pathlib import Path

from scripts import extract_clip_inbox as ext


def test_default_clip_prefers_mov(tmp_path: Path):
    media = tmp_path / "media"
    media.mkdir()
    (media / "backyard_weeds.MOV").write_bytes(b"x")
    (media / "backyard_weeds.mp4").write_bytes(b"y")
    found = ext.default_clip(media)
    assert found is not None
    assert found.name == "backyard_weeds.MOV"


def test_default_clip_missing(tmp_path: Path):
    assert ext.default_clip(tmp_path / "media") is None


def test_inbox_dest_lowercases_stem(tmp_path: Path):
    clip = tmp_path / "Backyard_Weeds.MOV"
    dest = ext.inbox_dest(clip, tmp_path / "inbox")
    assert dest == tmp_path / "inbox" / "backyard_weeds"


def test_dest_error_rejects_dataset_and_inbox_root(tmp_path: Path):
    inbox = tmp_path / "inbox"
    dataset = tmp_path / "dataset"
    inbox.mkdir()
    dataset.mkdir()
    assert ext.dest_error(inbox / "backyard_weeds", inbox, dataset) is None
    assert ext.dest_error(inbox, inbox, dataset) is not None
    assert ext.dest_error(dataset / "images" / "train", inbox, dataset) is not None
    assert ext.dest_error(tmp_path / "elsewhere", inbox, dataset) is not None


def test_ffmpeg_argv_video_only():
    clip = Path("/tmp/clip.MOV")
    dest = Path("/tmp/inbox/backyard_weeds")
    argv = ext.ffmpeg_argv(clip, dest, fps=1, quality=2)
    assert argv[0] == "ffmpeg"
    assert "-an" in argv
    assert "fps=1" in argv
    assert str(dest / "frame_%04d.jpg") == argv[-1]
    assert "0:v:0" in argv


def test_extract_skips_when_frames_exist(tmp_path: Path, capsys):
    inbox = tmp_path / "weeds" / "inbox"
    dataset = tmp_path / "weeds" / "dataset"
    dest = inbox / "backyard_weeds"
    dest.mkdir(parents=True)
    (dest / "frame_0001.jpg").write_bytes(b"jpg")
    clip = tmp_path / "clip.MOV"
    clip.write_bytes(b"mov")
    called: list[list[str]] = []

    def runner(argv):
        called.append(list(argv))
        return 0

    code = ext.extract(clip, dest, runner=runner, inbox=inbox, dataset=dataset)
    assert code == 0
    assert called == []
    assert (dest / "SOURCE.md").is_file()
    assert "domain val" in (dest / "SOURCE.md").read_text()
    assert "skip extract" in capsys.readouterr().out


def test_extract_runs_ffmpeg_when_empty(tmp_path: Path):
    inbox = tmp_path / "weeds" / "inbox"
    dataset = tmp_path / "weeds" / "dataset"
    dest = inbox / "backyard_weeds"
    clip = tmp_path / "clip.MOV"
    clip.write_bytes(b"mov")

    def runner(argv):
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "frame_0001.jpg").write_bytes(b"jpg")
        (dest / "frame_0002.jpg").write_bytes(b"jpg")
        assert argv[0] == "ffmpeg"
        return 0

    code = ext.extract(clip, dest, runner=runner, inbox=inbox, dataset=dataset)
    assert code == 0
    assert len(ext.existing_frames(dest)) == 2
    assert (dest / "SOURCE.md").is_file()


def test_extract_force_replaces_frames(tmp_path: Path):
    inbox = tmp_path / "weeds" / "inbox"
    dataset = tmp_path / "weeds" / "dataset"
    dest = inbox / "backyard_weeds"
    dest.mkdir(parents=True)
    stale = dest / "frame_0001.jpg"
    stale.write_bytes(b"old")
    clip = tmp_path / "clip.MOV"
    clip.write_bytes(b"mov")

    def runner(_argv):
        (dest / "frame_0001.jpg").write_bytes(b"new")
        return 0

    code = ext.extract(clip, dest, force=True, runner=runner, inbox=inbox, dataset=dataset)
    assert code == 0
    assert stale.read_bytes() == b"new"


def test_extract_rejects_dataset_dest(tmp_path: Path):
    inbox = tmp_path / "weeds" / "inbox"
    dataset = tmp_path / "weeds" / "dataset"
    dest = dataset / "images" / "train"
    dest.mkdir(parents=True)
    clip = tmp_path / "clip.MOV"
    clip.write_bytes(b"x")
    assert ext.extract(clip, dest, runner=lambda _a: 0, inbox=inbox, dataset=dataset) == 2


def test_main_missing_clip(tmp_path: Path):
    assert ext.main(["--clip", str(tmp_path / "missing.MOV")]) == 2


def test_extract_dry_run_prints_argv(tmp_path: Path, capsys):
    inbox = tmp_path / "weeds" / "inbox"
    dataset = tmp_path / "weeds" / "dataset"
    dest = inbox / "backyard_weeds"
    clip = tmp_path / "clip.MOV"
    clip.write_bytes(b"x")
    called: list[list[str]] = []
    code = ext.extract(
        clip,
        dest,
        dry_run=True,
        runner=lambda argv: called.append(list(argv)) or 0,
        inbox=inbox,
        dataset=dataset,
    )
    assert code == 0
    assert called == []
    out = capsys.readouterr().out
    assert "ffmpeg" in out
    assert not dest.exists()


def test_main_dry_run_default_clip(capsys):
    clip = ext.default_clip()
    assert clip is not None
    assert ext.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "ffmpeg" in out
    assert "fps=1" in out
