"""promote_inbox: split by image, copy jpg+txt, skip unlabeled."""

from pathlib import Path

from scripts import promote_inbox as promo


def test_frame_index():
    assert promo.frame_index("frame_0007") == 7
    assert promo.frame_index("frame_0061") == 61
    assert promo.frame_index("dandelion_1") is None


def test_assign_split_backyard_holdouts():
    assert promo.assign_split("frame_0007", "backyard_weeds") == "val"
    assert promo.assign_split("frame_0038", "backyard_weeds") == "val"
    assert promo.assign_split("frame_0022", "backyard_weeds") == "val"
    assert promo.assign_split("frame_0006", "backyard_weeds") == "train"
    assert promo.assign_split("frame_0011", "backyard_weeds") == "train"


def test_assign_split_other_inbox_is_val():
    assert promo.assign_split("anything", "dandelion") == "val"


def test_dest_stem_prefixes_source():
    assert promo.dest_stem("backyard_weeds", Path("frame_0007.jpg")) == (
        "backyard_weeds_frame_0007"
    )


def test_list_pairs_requires_sidecar(tmp_path: Path):
    folder = tmp_path / "inbox"
    folder.mkdir()
    (folder / "frame_0001.jpg").write_bytes(b"jpg")
    (folder / "frame_0002.jpg").write_bytes(b"jpg")
    (folder / "frame_0002.txt").write_text("")
    pairs = promo.list_pairs(folder)
    assert [p[0].name for p in pairs] == ["frame_0002.jpg"]


def test_promote_copies_train_and_val(tmp_path: Path):
    inbox = tmp_path / "inbox"
    dataset = tmp_path / "dataset"
    src = inbox / "backyard_weeds"
    src.mkdir(parents=True)
    (src / "frame_0006.jpg").write_bytes(b"a")
    (src / "frame_0006.txt").write_text("2 0.5 0.5 0.2 0.2\n")
    (src / "frame_0007.jpg").write_bytes(b"b")
    (src / "frame_0007.txt").write_text("2 0.5 0.5 0.2 0.2\n")
    (src / "frame_0001.jpg").write_bytes(b"c")
    (src / "frame_0001.txt").write_text("")
    assert promo.promote(inbox=inbox, dataset=dataset, source="backyard_weeds") == 0
    train_img = dataset / "images" / "train" / "backyard_weeds_frame_0006.jpg"
    val_img = dataset / "images" / "val" / "backyard_weeds_frame_0007.jpg"
    neg = dataset / "images" / "val" / "backyard_weeds_frame_0001.jpg"
    assert train_img.is_file()
    assert val_img.is_file()
    assert neg.is_file()
    assert (
        (dataset / "labels" / "train" / "backyard_weeds_frame_0006.txt")
        .read_text()
        .startswith("2 ")
    )
    assert (dataset / "labels" / "val" / "backyard_weeds_frame_0001.txt").read_text() == ""


def test_promote_skip_without_force(tmp_path: Path):
    inbox = tmp_path / "inbox"
    dataset = tmp_path / "dataset"
    src = inbox / "backyard_weeds"
    src.mkdir(parents=True)
    (src / "frame_0006.jpg").write_bytes(b"a")
    (src / "frame_0006.txt").write_text("0 0.5 0.5 0.1 0.1\n")
    assert promo.promote(inbox=inbox, dataset=dataset, source="backyard_weeds") == 0
    (src / "frame_0006.txt").write_text("0 0.9 0.9 0.1 0.1\n")
    assert promo.promote(inbox=inbox, dataset=dataset, source="backyard_weeds") == 0
    dest = dataset / "labels" / "train" / "backyard_weeds_frame_0006.txt"
    assert dest.read_text().startswith("0 0.5")
    assert promo.promote(inbox=inbox, dataset=dataset, source="backyard_weeds", force=True) == 0
    assert dest.read_text().startswith("0 0.9")


def test_promote_empty_folder(tmp_path: Path):
    inbox = tmp_path / "inbox"
    (inbox / "backyard_weeds").mkdir(parents=True)
    assert promo.promote(inbox=inbox, dataset=tmp_path / "dataset") == 2
