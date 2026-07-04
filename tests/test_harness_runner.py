from __future__ import annotations

from src.harness.config import load_experiment_config
from src.harness.runner import build_stage_commands, create_run_dir


def test_build_all_stage_commands_with_skip_train(tmp_path):
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    commands = build_stage_commands(
        config=config,
        stage="all",
        run_dir=tmp_path / "run",
        skip_train=True,
        model_path="runs/detect/train/weights/best.pt",
    )

    command_text = [" ".join(command) for command in commands]
    assert any("convert_visdrone_to_yolo.py" in item for item in command_text)
    assert not any("src.train" in item for item in command_text)
    assert any("src.val" in item for item in command_text)


def test_build_audit_only_commands(tmp_path):
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    commands = build_stage_commands(
        config=config,
        stage="audit",
        run_dir=tmp_path / "run",
        skip_train=False,
        model_path=None,
    )

    assert len(commands) == 1
    assert commands[0][1:] == [
        "-m",
        "src.harness.audit_data",
        "--config",
        str(config.path),
        "--format",
        "json",
        "--output",
        str(tmp_path / "run" / "audit.json"),
    ]


def test_create_run_dir_uses_experiment_name(tmp_path):
    config = load_experiment_config("configs/experiments/baseline_yolov8n.yaml")
    run_dir = create_run_dir(config, outputs_root=tmp_path, timestamp="20260704_120000")

    assert run_dir == tmp_path / "baseline_yolov8n" / "20260704_120000"
    assert run_dir.is_dir()
