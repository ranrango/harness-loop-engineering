# 无人机目标检测 — Makefile
# 用法：make <目标>

PYTHON ?= python3
DATA_ROOT ?= data

.PHONY: help install install-dev test lint format convert train val

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
