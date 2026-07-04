"""Experiment configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when an experiment config is missing required fields or has invalid types."""


@dataclass(frozen=True)
class ExperimentSection:
    name: str
    description: str = ""


@dataclass(frozen=True)
class DataSection:
    root: Path
    dataset_yaml: Path
    splits: list[str]
    image_ext: str
    require_labels: bool


@dataclass(frozen=True)
class ModelSection:
    weights: str


@dataclass(frozen=True)
class TrainSection:
    enabled: bool
    epochs: int
    batch: int
    imgsz: int
    device: str
    workers: int
    patience: int


@dataclass(frozen=True)
class ValSection:
    enabled: bool
    batch: int
    imgsz: int
    device: str
    conf: float
    iou: float


@dataclass(frozen=True)
class GatesSection:
    map50_min: float
    map_min: float
    precision_min: float
    recall_min: float
    allowed_drop: float

    def thresholds(self) -> dict[str, float]:
        return {
            "precision": self.precision_min,
            "recall": self.recall_min,
            "map50": self.map50_min,
            "map": self.map_min,
        }


@dataclass(frozen=True)
class OutputsSection:
    root: Path


@dataclass(frozen=True)
class ExperimentConfig:
    path: Path
    experiment: ExperimentSection
    data: DataSection
    model: ModelSection
    train: TrainSection
    val: ValSection
    gates: GatesSection
    outputs: OutputsSection


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"无法读取实验配置：{config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML 解析失败：{config_path}") from exc

    root = _mapping(raw, "config")
    experiment = _mapping(root.get("experiment"), "experiment")
    data = _mapping(root.get("data"), "data")
    model = _mapping(root.get("model"), "model")
    train = _mapping(root.get("train"), "train")
    val = _mapping(root.get("val"), "val")
    gates = _mapping(root.get("gates"), "gates")
    outputs = _mapping(root.get("outputs"), "outputs")

    return ExperimentConfig(
        path=config_path,
        experiment=ExperimentSection(
            name=_string(experiment.get("name"), "experiment.name"),
            description=_optional_string(experiment.get("description"), "experiment.description"),
        ),
        data=DataSection(
            root=Path(_string(data.get("root"), "data.root")),
            dataset_yaml=Path(_string(data.get("dataset_yaml"), "data.dataset_yaml")),
            splits=_string_list(data.get("splits"), "data.splits"),
            image_ext=_string(data.get("image_ext"), "data.image_ext").lstrip("."),
            require_labels=_bool(data.get("require_labels"), "data.require_labels"),
        ),
        model=ModelSection(weights=_string(model.get("weights"), "model.weights")),
        train=TrainSection(
            enabled=_bool(train.get("enabled"), "train.enabled"),
            epochs=_int(train.get("epochs"), "train.epochs"),
            batch=_int(train.get("batch"), "train.batch"),
            imgsz=_int(train.get("imgsz"), "train.imgsz"),
            device=_string(train.get("device"), "train.device"),
            workers=_int(train.get("workers"), "train.workers"),
            patience=_int(train.get("patience"), "train.patience"),
        ),
        val=ValSection(
            enabled=_bool(val.get("enabled"), "val.enabled"),
            batch=_int(val.get("batch"), "val.batch"),
            imgsz=_int(val.get("imgsz"), "val.imgsz"),
            device=_string(val.get("device"), "val.device"),
            conf=_float(val.get("conf"), "val.conf"),
            iou=_float(val.get("iou"), "val.iou"),
        ),
        gates=GatesSection(
            map50_min=_float(gates.get("map50_min"), "gates.map50_min"),
            map_min=_float(gates.get("map_min"), "gates.map_min"),
            precision_min=_float(gates.get("precision_min"), "gates.precision_min"),
            recall_min=_float(gates.get("recall_min"), "gates.recall_min"),
            allowed_drop=_float(gates.get("allowed_drop"), "gates.allowed_drop"),
        ),
        outputs=OutputsSection(root=Path(_string(outputs.get("root"), "outputs.root"))),
    )


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{field} 必须是 mapping")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field} 必须是非空字符串")
    return value


def _optional_string(value: Any, field: str) -> str:
    if value is None:
        return ""
    return _string(value, field)


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ConfigError(f"{field} 必须是非空字符串列表")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ConfigError(f"{field} 必须只包含非空字符串")
    return list(value)


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{field} 必须是布尔值")
    return value


def _int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field} 必须是整数")
    return value


def _float(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{field} 必须是数字")
    return float(value)
