"""weed-spray-train: empty dataset counting and --list-sources (no download)."""

from pathlib import Path

from weed_spray.vision import train as train_mod


def test_count_images_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(train_mod, "ROOT", tmp_path)
    assert train_mod._count_images("train") == 0
    (tmp_path / "weeds" / "dataset" / "images" / "train").mkdir(parents=True)
    (tmp_path / "weeds" / "dataset" / "images" / "train" / "a.jpg").write_bytes(b"x")
    (tmp_path / "weeds" / "dataset" / "images" / "train" / "notes.txt").write_text("no")
    monkeypatch.setattr(train_mod, "ROOT", tmp_path)
    assert train_mod._count_images("train") == 1


def test_main_list_sources(capsys):
    assert train_mod.main(["--list-sources"]) == 0
    out = capsys.readouterr().out
    assert "dandelion" in out
    assert "Do not download" in out


def test_main_empty_dataset_returns_2():
    assert train_mod.main([]) == 2


def test_yaml_has_all_classes():
    text = train_mod.YAML.read_text()
    for name in ("dandelion", "clover", "thistle"):
        assert name in text


def test_repo_root_finds_yaml():
    root = train_mod.repo_root()
    assert (root / "weeds" / "weeds.yaml").is_file()
    assert Path(train_mod.YAML).name == "weeds.yaml"
