# 无人机目标检测（Drone Object Detection）

[![CI](https://github.com/ranrango/drone-object-detection/actions/workflows/ci.yml/badge.svg)](https://github.com/ranrango/drone-object-detection/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/许可证-MIT-green)](LICENSE)
[![YOLOv8](https://img.shields.io/badge/模型-YOLOv8n-orange)](https://github.com/ultralytics/ultralytics)

基于 [VisDrone2019-DET](http://aiskyeye.com/) 数据集，使用 YOLOv8 构建无人机航拍图像中的**小目标检测基线**。

本仓库只包含源代码、配置文件和复现文档。数据集、训练输出、模型权重和凭据文件均不纳入版本控制。

---

## 实验结果

| 指标 | 数值 |
|---|---:|
| 精确率（Precision） | 0.354 |
| 召回率（Recall） | 0.274 |
| **mAP@0.5** | **0.258** |
| mAP@0.5:0.95 | 0.147 |

*基线配置：YOLOv8n · 10 epoch · batch=8 · imgsz=640 · CPU*

<details>
<summary>逐类 AP@0.5</summary>

| 类别 | AP@0.5 |
|---|---:|
| 轿车 | 0.686 |
| 公交车 | 0.333 |
| 面包车 | 0.282 |
| 行人 | 0.266 |
| 摩托车 | 0.262 |
| 人群 | 0.215 |
| 卡车 | 0.231 |
| 三轮车 | 0.172 |
| 遮阳三轮车 | 0.082 |
| 自行车 | 0.045 |

</details>

样本推理结果：

![样本推理图](assets/codex_predict_bestpt_image_2.jpg)

训练曲线与评估图表：

| 训练指标曲线 | 混淆矩阵 |
|---|---|
| ![results](assets/results.png) | ![confusion](assets/confusion_matrix.png) |

![PR 曲线](assets/BoxPR_curve.png)

---

## 快速开始

```bash
# 1. 克隆并安装
git clone https://github.com/ranrango/drone-object-detection
cd drone-object-detection
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. 下载 VisDrone2019-DET 数据集并放置到 data/ 目录
#    目录结构见下方"数据集"章节。

# 3. 转换标注格式
drone-convert

# 4. 训练
drone-train --epochs 10 --batch 8 --device cpu

# 5. 验证
drone-val --model runs/detect/train_<日期>_yolov8n_visdrone/weights/best.pt

# 6. 推理
drone-detect --model runs/detect/.../weights/best.pt --source 图片路径.jpg
```

也可以使用 Makefile 快捷命令：

```bash
make install-dev   # 安装项目及开发依赖
make test          # 运行单元测试（不需要 GPU）
make convert       # 转换标注
make train         # 10 epoch 基线训练
make val           # 验证最新权重
```

## Harness 与 Loop 工程化

本项目提供一套轻量实验线束，用于把数据审计、训练、验证、指标门槛和报告产物串成可重复闭环。

```bash
make audit            # 检查本地 VisDrone/YOLO 数据结构和标签质量
make harness-dry-run  # 打印完整闭环命令，不执行训练
make metrics-check    # 用 baseline 指标检查 gate
```

默认实验配置位于 `configs/experiments/baseline_yolov8n.yaml`。完整说明见
[`docs/harness_loop.md`](docs/harness_loop.md)。

---

## 数据集

**VisDrone2019-DET** — 无人机视角下的 10 类目标检测数据集。

请从 [VisDrone 官网](http://aiskyeye.com/) 下载并确认许可条款后使用。数据集不包含在本仓库中。

下载并转换后的目录结构：

```
data/
  VisDrone2019-DET-train/
    images/          # 6,471 张图片
    annotations/     # 原始 VisDrone 标注文件
    labels/          # YOLO 格式标注文件（由转换脚本生成）
  VisDrone2019-DET-val/
    images/          # 548 张图片
    annotations/
    labels/
  VisDrone2019-DET-test/
    images/
```

目标类别：

| ID | 类别 | ID | 类别 |
|---:|---|---:|---|
| 0 | 行人 | 5 | 卡车 |
| 1 | 人群 | 6 | 三轮车 |
| 2 | 自行车 | 7 | 遮阳三轮车 |
| 3 | 轿车 | 8 | 公交车 |
| 4 | 面包车 | 9 | 摩托车 |

---

## 安装

要求 Python 3.9 及以上版本。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

安装开发依赖（代码检查、测试、Notebook）：

```bash
pip install -e ".[dev]"
```

安装 DeepSeek smoke test 依赖：

```bash
pip install -e ".[smoke]"
```

---

## 命令行工具

执行 `pip install -e .` 后，以下命令自动可用：

### `drone-convert` — 转换标注

```
drone-convert [--data-root 路径] [--splits 切分名 ...] [--img-ext 扩展名]

选项：
  --data-root   包含 VisDrone 切分子目录的根路径        （默认：data）
  --splits      要转换的一个或多个切分                   （默认：train val）
  --img-ext     图片扩展名，不含点号                     （默认：jpg）
```

### `drone-train` — 训练

```
drone-train [--model 模型] [--data 配置] [--epochs N] [--batch N]
            [--imgsz N] [--device 设备] [--project 目录] [--name 名称]
            [--workers N] [--patience N] [--exist-ok]

默认值：model=yolov8n.pt  epochs=10  batch=8  imgsz=640  device=cpu
```

### `drone-val` — 验证

```
drone-val --model 权重路径 [--data 配置] [--imgsz N] [--batch N]
          [--device 设备] [--conf 阈值] [--iou 阈值]
          [--project 目录] [--name 名称] [--exist-ok]
```

### `drone-detect` — 推理

```
drone-detect --model 权重路径 --source 输入源 [--imgsz N] [--conf 阈值] [--iou 阈值]
             [--device 设备] [--classes 类别ID ...] [--save-txt] [--no-save]
             [--project 目录] [--name 名称] [--exist-ok]

示例：
  drone-detect --model best.pt --source image.jpg
  drone-detect --model best.pt --source images/ --classes 3 4 8   # 只检测轿车/面包车/公交车
  drone-detect --model best.pt --source video.mp4 --conf 0.3 --save-txt
```

---

## 项目结构

```
drone-object-detection/
├── src/
│   ├── __init__.py          # 包标识，版本号
│   ├── detect.py            # drone-detect 入口
│   ├── train.py             # drone-train 入口
│   ├── val.py               # drone-val 入口
│   └── utils.py             # 共用工具函数
├── scripts/
│   └── convert_visdrone_to_yolo.py   # 标注格式转换脚本
├── tests/
│   ├── conftest.py          # 测试夹具
│   ├── image_helpers.py     # 合成图片生成工具
│   ├── test_convert.py      # 转换逻辑测试
│   ├── test_cli.py          # 命令行参数解析测试
│   └── test_utils.py        # 工具函数测试
├── docs/
│   ├── environment.md       # 环境配置说明
│   └── reproducibility.md   # 逐步复现指南
├── assets/                  # README 展示用结果图
├── .github/workflows/ci.yml # GitHub Actions：代码检查 + 测试
├── data.yaml                # 数据集配置
├── pyproject.toml           # 包元数据、依赖、工具配置
├── Makefile                 # 快捷命令
├── CHANGELOG.md             # 变更记录
├── CONTRIBUTING.md          # 贡献指南
├── LICENSE                  # MIT 许可证
└── .env.example             # 凭据配置模板
```

---

## 开发

```bash
# 运行测试（不需要 GPU）
make test

# 代码检查
make lint

# 格式检查
make format

# 自动修复格式
black src/ scripts/ tests/
```

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 复现基线

完整步骤见 [docs/reproducibility.md](docs/reproducibility.md)。

简短版本：

```bash
make convert   # 转换 VisDrone 标注
make train     # CPU 上训练 YOLOv8n，10 个 epoch
make val       # 在 val 集上验证
```

验证输出示例：

```
────────────────────────────────────────
  mAP@0.5      : 0.2576
  mAP@0.5:0.95 : 0.1468
  精确率       : 0.3538
  召回率       : 0.2740
────────────────────────────────────────
```

---

## 已知局限

- **模型规模**：YOLOv8n 是最小变体；自行车、遮阳三轮车等小目标类别的 AP 较低。
- **训练预算**：CPU 上仅跑 10 个 epoch；使用 GPU 并延长至 50–100 epoch 可显著提升 mAP。
- **未调整数据增强**：使用 Ultralytics 默认配置，未针对小目标做专项优化。
- **测试集**：VisDrone 官方未公开测试集标注；本项目所有指标均基于 val 集。

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

VisDrone2019-DET 数据集有独立许可证，使用前请查阅 [aiskyeye.com](http://aiskyeye.com/)。  
YOLOv8 预训练权重（yolov8n.pt）遵循 [Ultralytics 许可证](https://github.com/ultralytics/ultralytics/blob/main/LICENSE)。
