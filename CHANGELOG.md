# 变更记录

本文件记录项目的所有重要变更，格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

## [未发布]

### 新增
- `src/train.py` — 训练命令行入口，支持自动生成 run 名称、早停、线程数配置
- `src/val.py` — 验证命令行入口，终端直接输出指标汇总表
- `src/utils.py` — 共用工具：`VISDRONE_CLASSES`、`resolve_model`、`build_run_name`
- `src/__init__.py` — 包标识文件，包含版本号
- `tests/` — 25 个单元测试，覆盖转换逻辑、图片头解析、命令行参数解析和工具函数；无需安装 torch/ultralytics 即可运行
- `Makefile` — 快捷命令：`install`、`install-dev`、`test`、`lint`、`format`、`convert`、`train`、`val`
- `.github/workflows/ci.yml` — GitHub Actions CI：ruff + black 代码检查 + pytest（Python 3.9/3.10/3.11）
- `LICENSE` — MIT 许可证
- `.env.example` — 凭据配置模板
- `CHANGELOG.md` — 本文件
- `CONTRIBUTING.md` — 贡献指南

### 变更
- `src/detect.py` — 新增 `--iou`、`--classes`、`--save-txt`、`--no-save` 参数；输出各类别检测数量；使用共用 `utils.py`；run 名称自动生成
- `scripts/convert_visdrone_to_yolo.py` — 重写：新增 CLI 参数（`--data-root`、`--splits`、`--img-ext`）；只读图片文件头获取尺寸（无需 cv2）；超出边界的框自动截断；转换进度实时输出；`ConvertStats` 统计数据类
- `pyproject.toml` — 新增 4 个命令行入口（`drone-detect`/`train`/`val`/`convert`）、`dev` 扩展依赖、ruff/black/pytest 配置、分类信息和项目链接

## [0.1.0] — 2025-11-20

### 新增
- 项目初始化：`pyproject.toml`、`data.yaml`、`.gitignore`
- `scripts/convert_visdrone_to_yolo.py` — VisDrone 到 YOLO 格式转换脚本首版
- `src/detect.py` — YOLOv8 推理命令行工具
- VisDrone2019-DET 数据流程和 10 epoch YOLOv8n 基线训练
- 基线指标：mAP@0.5 = 0.258，mAP@0.5:0.95 = 0.147
