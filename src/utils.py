"""src/ 各脚本共用的工具函数。"""

from __future__ import annotations

from pathlib import Path

# VisDrone2019-DET 的 10 个目标类别（0-based）
VISDRONE_CLASSES: dict[int, str] = {
    0: "行人",
    1: "人群",
    2: "自行车",
    3: "轿车",
    4: "面包车",
    5: "卡车",
    6: "三轮车",
    7: "遮阳三轮车",
    8: "公交车",
    9: "摩托车",
}


def resolve_model(model_arg: str) -> Path:
    """返回模型文件的 Path 对象；文件不存在时抛出 FileNotFoundError。"""
    p = Path(model_arg)
    if not p.exists():
        raise FileNotFoundError(f"模型文件不存在：{p}")
    return p


def build_run_name(prefix: str, model_stem: str, suffix: str = "visdrone") -> str:
    """构造带日期的 run 名称，避免覆盖历史实验。

    示例：'train_20260630_yolov8n_visdrone'
    """
    from datetime import date

    today = date.today().strftime("%Y%m%d")
    return f"{prefix}_{today}_{model_stem}_{suffix}"
