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
    for name in ("dandelion", "clover", "thistle", "mallow"):
        assert name in text


def test_repo_root_finds_yaml():
    root = train_mod.repo_root()
    assert (root / "weeds" / "weeds.yaml").is_file()
    assert Path(train_mod.YAML).name == "weeds.yaml"


def _mini_dataset(tmp_path: Path, train_labels: str) -> None:
    for split in ("train", "val"):
        (tmp_path / "weeds" / "dataset" / "images" / split).mkdir(parents=True)
        (tmp_path / "weeds" / "dataset" / "labels" / split).mkdir(parents=True)
        (tmp_path / "weeds" / "dataset" / "images" / split / "a.jpg").write_bytes(b"x")
    (tmp_path / "weeds" / "dataset" / "labels" / "train" / "a.txt").write_text(train_labels)
    (tmp_path / "weeds" / "dataset" / "labels" / "val" / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n")
    (tmp_path / "weeds" / "weeds.yaml").write_text("names: dandelion clover thistle mallow\n")


def test_train_refuses_a_class_with_no_boxes(tmp_path, monkeypatch, capsys):
    _mini_dataset(
        tmp_path,
        "0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.2 0.2\n2 0.3 0.3 0.2 0.2\n",
    )
    monkeypatch.setattr(train_mod, "ROOT", tmp_path)
    monkeypatch.setattr(train_mod, "YAML", tmp_path / "weeds" / "weeds.yaml")
    assert train_mod.main([]) == 2
    assert "mallow" in capsys.readouterr().err


def test_train_calls_yolo_when_every_class_has_a_box(tmp_path, monkeypatch):
    _mini_dataset(
        tmp_path,
        "0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.2 0.2\n2 0.3 0.3 0.2 0.2\n3 0.2 0.2 0.2 0.2\n",
    )
    monkeypatch.setattr(train_mod, "ROOT", tmp_path)
    monkeypatch.setattr(train_mod, "YAML", tmp_path / "weeds" / "weeds.yaml")
    called: dict[str, object] = {}

    class FakeYOLO:
        def __init__(self, model: str) -> None:
            called["model"] = model

        def train(self, **kwargs: object) -> None:
            called["data"] = kwargs["data"]

    monkeypatch.setattr(train_mod, "load_yolo", lambda: FakeYOLO)
    assert train_mod.main([]) == 0
    assert called["model"] == "yolov8n.pt"
    assert called["data"] == str(tmp_path / "weeds" / "weeds.yaml")


def test_missing_train_classes_ignores_orphan_labels(tmp_path, monkeypatch):
    """Orphan labels/train/*.txt without a paired image must not clear the gate.

    Ultralytics only stem-pairs labels to images/train/*; leftovers with ids
    0-3 must not make missing_train_classes return [].
    """
    images = tmp_path / "weeds" / "dataset" / "images" / "train"
    labels = tmp_path / "weeds" / "dataset" / "labels" / "train"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    # Paired negative-only sample (YOLO would train this as empty).
    (images / "a.jpg").write_bytes(b"x")
    (labels / "a.txt").write_text("")
    # Orphan label with all four classes — no images/train/orphan.*
    (labels / "orphan.txt").write_text(
        "0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.2 0.2\n2 0.3 0.3 0.2 0.2\n3 0.2 0.2 0.2 0.2\n"
    )
    monkeypatch.setattr(train_mod, "ROOT", tmp_path)
    missing = train_mod.missing_train_classes()
    assert missing == ["dandelion", "clover", "thistle", "mallow"]


def test_missing_train_classes_counts_paired_labels_only(tmp_path, monkeypatch):
    """Paired image+label rows still clear those classes from missing."""
    images = tmp_path / "weeds" / "dataset" / "images" / "train"
    labels = tmp_path / "weeds" / "dataset" / "labels" / "train"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    (images / "a.jpg").write_bytes(b"x")
    (labels / "a.txt").write_text(
        "0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.2 0.2\n2 0.3 0.3 0.2 0.2\n3 0.2 0.2 0.2 0.2\n"
    )
    # Orphan with nothing useful — must not matter either way when paired is complete.
    (labels / "orphan.txt").write_text("0 0.1 0.1 0.1 0.1\n")
    monkeypatch.setattr(train_mod, "ROOT", tmp_path)
    assert train_mod.missing_train_classes() == []


def test_train_refuses_when_only_orphan_labels_have_classes(tmp_path, monkeypatch, capsys):
    """train() must exit 2 if only unpaired orphans carry class rows."""
    for split in ("train", "val"):
        (tmp_path / "weeds" / "dataset" / "images" / split).mkdir(parents=True)
        (tmp_path / "weeds" / "dataset" / "labels" / split).mkdir(parents=True)
        (tmp_path / "weeds" / "dataset" / "images" / split / "a.jpg").write_bytes(b"x")
    (tmp_path / "weeds" / "dataset" / "labels" / "train" / "a.txt").write_text("")
    (tmp_path / "weeds" / "dataset" / "labels" / "train" / "orphan.txt").write_text(
        "0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.2 0.2\n2 0.3 0.3 0.2 0.2\n3 0.2 0.2 0.2 0.2\n"
    )
    (tmp_path / "weeds" / "dataset" / "labels" / "val" / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n")
    (tmp_path / "weeds" / "weeds.yaml").write_text("names: dandelion clover thistle mallow\n")
    monkeypatch.setattr(train_mod, "ROOT", tmp_path)
    monkeypatch.setattr(train_mod, "YAML", tmp_path / "weeds" / "weeds.yaml")
    assert train_mod.main([]) == 2
    err = capsys.readouterr().err
    assert "clover" in err
    assert "mallow" in err


def test_missing_train_classes_counts_ultralytics_bmp_pair(tmp_path, monkeypatch):
    """Paired .bmp + labels must clear the gate (Ultralytics IMG_FORMATS includes bmp).

    Failure mode BugScout filed on #60: a.jpg (empty) + b.bmp with ids 0-3 must not
    treat b as orphan and exit-2 every class — Ultralytics would stem-pair b.bmp.
    """
    images = tmp_path / "weeds" / "dataset" / "images" / "train"
    labels = tmp_path / "weeds" / "dataset" / "labels" / "train"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    (images / "a.jpg").write_bytes(b"x")
    (labels / "a.txt").write_text("")
    (images / "b.bmp").write_bytes(b"BM")
    (labels / "b.txt").write_text(
        "0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.2 0.2\n2 0.3 0.3 0.2 0.2\n3 0.2 0.2 0.2 0.2\n"
    )
    monkeypatch.setattr(train_mod, "ROOT", tmp_path)
    assert train_mod.missing_train_classes() == []


def test_missing_train_classes_ignores_non_ultralytics_image_ext(tmp_path, monkeypatch):
    """Label paired only to a non-IMG_FORMATS file (e.g. .xyz) stays orphan."""
    images = tmp_path / "weeds" / "dataset" / "images" / "train"
    labels = tmp_path / "weeds" / "dataset" / "labels" / "train"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    (images / "a.jpg").write_bytes(b"x")
    (labels / "a.txt").write_text("")
    (images / "ghost.xyz").write_bytes(b"nope")
    (labels / "ghost.txt").write_text(
        "0 0.5 0.5 0.2 0.2\n1 0.4 0.4 0.2 0.2\n2 0.3 0.3 0.2 0.2\n3 0.2 0.2 0.2 0.2\n"
    )
    monkeypatch.setattr(train_mod, "ROOT", tmp_path)
    assert train_mod.missing_train_classes() == [
        "dandelion",
        "clover",
        "thistle",
        "mallow",
    ]
