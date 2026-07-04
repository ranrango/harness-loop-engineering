# 无人机目标检测 — Makefile
# 用法：make <目标>

PYTHON ?= python3
DATA_ROOT ?= data
HARNESS_CONFIG ?= configs/experiments/baseline_yolov8n.yaml

.PHONY: help install install-dev test lint format convert train val audit harness-dry-run metrics-check

help:
	@echo "可用命令："
	@echo "  install      安装项目依赖"
	@echo "  install-dev  安装项目及开发依赖"
	@echo "  test         运行所有单元测试"
	@echo "  lint         运行 ruff 代码检查"
	@echo "  format       运行 black 格式检查（只读）"
	@echo "  convert      将 VisDrone 标注转换为 YOLO 格式"
	@echo "  train        运行基线训练（CPU，10 epoch，YOLOv8n）"
	@echo "  val          验证最新的 best.pt 权重"
	@echo "  audit        运行 harness 数据审计"
	@echo "  harness-dry-run  打印完整 harness 闭环命令但不训练"
	@echo "  metrics-check     使用命令行指标检查 baseline gate"

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/ --tb=short -q

lint:
	ruff check src/ scripts/ tests/

format:
	black --check src/ scripts/ tests/

convert:
	$(PYTHON) scripts/convert_visdrone_to_yolo.py --data-root $(DATA_ROOT)

train:
	yolo detect train \
		model=yolov8n.pt \
		data=data.yaml \
		epochs=10 \
		batch=8 \
		imgsz=640 \
		device=cpu \
		project=runs/detect \
		exist_ok=False

val:
	@latest=$$(ls -td runs/detect/train_*/weights/best.pt 2>/dev/null | head -1); \
	if [ -z "$$latest" ]; then echo "在 runs/detect/ 下未找到训练权重"; exit 1; fi; \
	yolo detect val \
		model=$$latest \
		data=data.yaml \
		imgsz=640 \
		batch=8 \
		device=cpu \
		project=runs/detect \
		exist_ok=False

audit:
	$(PYTHON) -m src.harness.audit_data --config $(HARNESS_CONFIG) --data-root $(DATA_ROOT)

harness-dry-run:
	$(PYTHON) -m src.harness.runner --config $(HARNESS_CONFIG) --stage all --dry-run --skip-train --model runs/detect/train/weights/best.pt

metrics-check:
	$(PYTHON) -m src.harness.metrics --config $(HARNESS_CONFIG) --precision 0.354 --recall 0.274 --map50 0.258 --map 0.147
