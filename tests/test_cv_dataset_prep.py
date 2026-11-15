"""Tests for the YOLO dataset scaffolding script."""

from pathlib import Path

from cv_module.dataset_preparation import setup_yolo_dataset


def _config_text(yaml_path: Path) -> str:
    return yaml_path.read_text(encoding="utf-8")


def test_creates_the_expected_directory_tree(tmp_path):
    dataset = tmp_path / "dataset"
    setup_yolo_dataset(dataset)

    for split in ("train", "val", "test"):
        assert (dataset / "images" / split).is_dir()
        assert (dataset / "labels" / split).is_dir()


def test_yaml_path_points_at_the_created_directory(tmp_path):
    dataset = tmp_path / "dataset"
    yaml_path = setup_yolo_dataset(dataset)

    assert yaml_path.is_file()
    lines = _config_text(yaml_path).splitlines()
    path_line = next(line for line in lines if line.startswith("path:"))
    assert path_line.split("path:", 1)[1].strip() == dataset.as_posix()


def test_yaml_declares_train_val_test_and_class_names(tmp_path):
    yaml_path = setup_yolo_dataset(tmp_path / "dataset")
    text = _config_text(yaml_path)

    for key in ("train: images/train", "val: images/val", "test: images/test"):
        assert key in text
    assert "names:" in text
    assert "0: resistor" in text


def test_rerunning_is_idempotent(tmp_path):
    dataset = tmp_path / "dataset"
    first = setup_yolo_dataset(dataset)
    second = setup_yolo_dataset(dataset)
    assert first == second
    assert first.is_file()
