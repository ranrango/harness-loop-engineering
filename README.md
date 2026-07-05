# Harness & Loop Engineering for Drone Object Detection

[![CI](https://github.com/ranrango/harness-loop-engineering/actions/workflows/ci.yml/badge.svg)](https://github.com/ranrango/harness-loop-engineering/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/ranrango/harness-loop-engineering)](https://github.com/ranrango/harness-loop-engineering/releases/tag/v0.1.0)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/许可证-MIT-green)](LICENSE)
[![YOLOv8](https://img.shields.io/badge/模型-YOLOv8n-orange)](https://github.com/ultralytics/ultralytics)

本仓库把 **Harness Engineering（驾驭工程）** 与 **Loop Engineering（循环工程）** 的方法论，落到一个可运行、可测试、可复现的无人机目标检测项目中。

- 概念层：系统整理 AI 应用中的 Harness/Loop 设计方法、组件和行业实践。
- 工程层：以 YOLOv8n/VisDrone 检测基线作为被控实验对象，而不是重新主张新的检测精度结论。
- 闭环层：用配置化实验、数据审计、训练、验证、指标门槛和报告生成形成可重复迭代流程。

本仓库只包含源代码、配置文件、示例结果和复现文档。数据集、训练输出、模型权重和凭据文件均不纳入版本控制。

## 快速入口

| 入口 | 说明 |
|---|---|
| [v0.1.0 Release](https://github.com/ranrango/harness-loop-engineering/releases/tag/v0.1.0) | 当前公开发布版本 |
| [Harness/Loop 使用说明](docs/harness_loop.md) | 数据审计、指标门槛、runner 和报告工作流 |
| [实践手册](PRACTICAL_GUIDE.md) | Harness/Loop 方法论从概念到落地 |
| [基线来源说明](#基线来源与本仓库侧重) | 区分检测基线与本仓库工程贡献 |
| [复现指南](docs/reproducibility.md) | VisDrone + YOLOv8n 基线复现步骤 |
| [Publication Checklist](PUBLICATION_CHECKLIST.md) | 发布安全边界和验证记录 |

---

## 什么是 Harness 与 Loop？

| | Harness Engineering | Loop Engineering |
|---|---|---|
| 中文 | 驾驭工程 | 循环工程 |
| 核心问题 | 如何让模型/系统可控、可预测地完成任务 | 如何构建感知、决策、行动、反馈的迭代闭环 |
| 关键词 | Prompt、Guardrails、Evals、RAG、Tool Use、指标门槛 | ReAct、Agent Loop、Human-in-the-Loop、监控、修复 |
| 在本项目中 | 配置、数据审计、训练/验证命令、质量门槛 | 每轮实验产物、指标比较、报告、下一步建议 |

Harness 是基础设施层，Loop 是迭代执行层。对于目标检测项目，它们对应的是：把数据、模型、训练、验证和报告变成可控管线，再用结果持续驱动下一轮实验。

---

## 目录结构

```text
harness-loop-engineering/
├── PRACTICAL_GUIDE.md          # 从概念到落地的实践手册
├── applications/               # 行业应用案例
├── harness/                    # 驾驭工程概念、组件、行业实践、示例
├── loop/                       # 循环工程概念、组件、行业实践、示例
├── configs/experiments/        # 检测实验配置
├── src/
│   ├── harness/                # 数据审计、指标检查、报告、runner
│   ├── detect.py               # drone-detect 入口
│   ├── train.py                # drone-train 入口
│   ├── val.py                  # drone-val 入口
│   └── utils.py
├── scripts/                    # VisDrone 标注转换脚本
├── tests/                      # 单元测试
├── docs/                       # 环境、复现、Harness/Loop 使用文档
├── assets/                     # README 展示用结果图
├── .github/workflows/ci.yml    # GitHub Actions：代码检查 + 测试
├── data.yaml                   # 数据集配置
├── pyproject.toml              # 包元数据、依赖、工具配置
└── Makefile                    # 快捷命令
```

---

## 快速导航

### Harness/Loop 方法论

| 章节 | 内容 |
|---|---|
| [实践手册](./PRACTICAL_GUIDE.md) | 如何把 Harness 与 Loop 落到真实 AI 应用 |
| [应用案例](./applications/) | 客服、代码、工业、研究等场景的组合设计 |
| [Harness 核心概念](./harness/01-concepts/) | 定义、起源、与传统工程的关系 |
| [Harness 核心组件](./harness/02-core-components/) | Prompt 工程、Guardrails、Evals、RAG、Tool Use |
| [Harness 工业实践](./harness/03-industry/) | 发展历程、各公司实践、前沿趋势 |
| [Harness 代码示例](./harness/04-examples/) | 可运行的工程实践示例 |
| [Loop 核心概念](./loop/01-concepts/) | Agent Loop 心智模型 |
| [Loop 核心组件](./loop/02-core-components/) | ReAct、Memory、Planning、Multi-Agent |
| [Loop 工业实践](./loop/03-industry/) | 发展历程、各公司实践、前沿趋势 |
| [Loop 代码示例](./loop/04-examples/) | 可运行的闭环示例 |

### 无人机检测工程

| 文档 | 内容 |
|---|---|
| [Harness/Loop 使用说明](docs/harness_loop.md) | 实验配置、数据审计、指标门槛、报告生成 |
| [环境配置](docs/environment.md) | Python、依赖和本地环境 |
| [复现指南](docs/reproducibility.md) | 从数据转换到训练验证的完整步骤 |
| [设计规格](docs/superpowers/specs/2026-07-04-harness-loop-engineering-design.zh.md) | 中文设计说明 |
| [实施计划](docs/superpowers/plans/2026-07-04-harness-loop-engineering.zh.md) | 中文实施计划 |

---

## 基线来源与本仓库侧重

本仓库的检测 baseline 继承自 [ranrango/drone-object-detection](https://github.com/ranrango/drone-object-detection) 的 YOLOv8n/VisDrone 工程线，用作 Harness/Loop 示例中的稳定被控对象。首页不展示检测性能结果，因为这些不是本仓库新增的检测精度贡献。

本仓库真正关注的问题是：

- 如何把一次目标检测实验描述成可审计、可复现的配置合约。
- 如何在训练/验证前后自动检查数据、命令、指标和产物。
- 如何把指标退化、数据异常和下一轮实验建议写入 loop report。
- 如何把人工审批点放在“是否晋级模型/是否启动昂贵训练/是否发布结果”这些决策处。

历史检测结果和复现细节保留在 [docs/reproducibility.md](docs/reproducibility.md) 与 [docs/results.csv](docs/results.csv)，用于工程闭环验证。

---

## Harness/Loop 工程示例

### 1. Harness：数据契约审计

```bash
drone-audit-data --config configs/experiments/baseline_yolov8n.yaml --format markdown
```

这个例子不训练模型，而是把数据集目录、图片/标签配对、类别 ID、空标签和标注格式作为实验前置合约检查。它回答的是“这轮实验能不能开始”，不是“模型精度是多少”。

### 2. Harness：指标门槛 Gate

```bash
drone-check-metrics \
  --config configs/experiments/baseline_yolov8n.yaml \
  --metrics runs/harness/<experiment>/<timestamp>/metrics.json
```

这个例子把验证输出当作机器可读的质量信号，与配置里的 gate 阈值比较。通过或失败都生成结构化结果，供 CI、报告和人工 review 使用。

### 3. Loop：实验闭环 Dry Run

```bash
drone-run-harness \
  --config configs/experiments/baseline_yolov8n.yaml \
  --stage all \
  --dry-run \
  --skip-train \
  --model runs/detect/train/weights/best.pt
```

这个例子展示一次完整 loop 会怎样编排：`audit -> train/val -> metric gate -> report`。`--dry-run` 只打印将要执行的步骤，适合在提交训练任务前做人工确认。

### 4. Loop：报告与下一轮建议

```bash
drone-loop-report \
  --config configs/experiments/baseline_yolov8n.yaml \
  --run-dir runs/harness/<experiment>/<timestamp>
```

这个例子把审计结果、验证指标、gate 状态和规则化建议汇总成 Markdown 报告。报告关注“下一轮该检查数据、调阈值、扩训练预算，还是停止发布”，让实验从一次性脚本变成可追踪的迭代闭环。
使用 `--run-dir` 时，CLI 会自动读取该目录下的 `audit.json`、`metrics.json` 和 `commands.txt`，并把 `resolved_config.yaml`、审计结果、指标、命令记录和报告本身列为可追溯产物。

---

## 快速开始

```bash
git clone https://github.com/ranrango/harness-loop-engineering
cd harness-loop-engineering
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

不下载数据、不准备权重，也可以先跑一个 Harness/Loop 自包含 demo：

```bash
drone-demo-loop --profile baseline
```

它会生成 `runs/harness-demo/harness_loop_demo/<timestamp>/`，包含 synthetic 数据审计、示例指标、命令记录和 `loop_report.md`。这个 demo 用来展示闭环工程产物，不代表检测模型性能。
如果要演示跨轮对比，可以生成两轮 demo run：

```bash
drone-demo-loop --profile baseline --timestamp baseline
drone-demo-loop --profile improved --timestamp improved
drone-compare-runs \
  --base-run runs/harness-demo/harness_loop_demo/baseline \
  --candidate-run runs/harness-demo/harness_loop_demo/improved
```

下载 VisDrone2019-DET 数据集并放置到 `data/` 目录后，运行：

```bash
drone-convert
drone-train --epochs 10 --batch 8 --device cpu
drone-val --model runs/detect/train_<日期>_yolov8n_visdrone/weights/best.pt
drone-detect --model runs/detect/.../weights/best.pt --source 图片路径.jpg
```

也可以使用 Makefile：

```bash
make install-dev      # 安装项目及开发依赖
make test             # 运行单元测试
make convert          # 转换 VisDrone 标注
make train            # 10 epoch 基线训练
make val              # 验证最新权重
make demo-loop        # 生成无需真实数据/权重的 Harness/Loop demo
make compare-runs     # 比较两轮 demo 或真实 harness run
```

---

## Harness 与 Loop 工作流

默认实验配置位于 `configs/experiments/baseline_yolov8n.yaml`。

```bash
make audit            # 检查本地 VisDrone/YOLO 数据结构和标签质量
make harness-dry-run  # 打印完整闭环命令，不执行训练
make metrics-check    # 用 baseline 指标检查 gate
```

常用 CLI：

```bash
drone-audit-data --config configs/experiments/baseline_yolov8n.yaml
drone-run-harness --config configs/experiments/baseline_yolov8n.yaml --stage audit --dry-run
drone-check-metrics --config configs/experiments/baseline_yolov8n.yaml --metrics runs/.../metrics.json
drone-loop-report --config configs/experiments/baseline_yolov8n.yaml --run-dir runs/harness/<experiment>/<timestamp>
drone-demo-loop --profile baseline
drone-compare-runs --base-run runs/harness/<old> --candidate-run runs/harness/<new>
```

闭环产物会写入 `runs/harness/<experiment>/<timestamp>/`，包括数据审计、验证指标、gate 检查和 Markdown 报告。
自包含 demo 产物会写入 `runs/harness-demo/harness_loop_demo/<timestamp>/`，用于快速查看报告结构和证据链。
跨轮对比报告会读取两次 run 的 `audit.json`、`metrics.json` 和 `commands.txt`，输出指标 delta、审计状态变化和下一步 loop 决策建议。

---

## 隐私与发布边界

- 不提交真实 `.env`、API key、token、私钥或本机路径。
- 不提交 VisDrone 原始数据、训练输出、模型权重或导出的推理结果目录。
- `.env.example` 只保留空值占位；真实凭据只应存在于本地 shell、CI secrets 或未跟踪的 `.env` 文件中。
- 发布前使用 `PUBLICATION_CHECKLIST.md` 中的检查项确认公开仓库内容。

---

## 数据集

**VisDrone2019-DET** 是无人机视角下的 10 类目标检测数据集。请从 [VisDrone 官网](http://aiskyeye.com/) 下载并确认许可条款后使用。

下载并转换后的目录结构：

```text
data/
  VisDrone2019-DET-train/
    images/
    annotations/
    labels/
  VisDrone2019-DET-val/
    images/
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

## 命令行工具

执行 `pip install -e .` 后，以下命令自动可用：

```text
drone-convert        转换 VisDrone 标注为 YOLO 格式
drone-train          训练 YOLOv8 检测模型
drone-val            验证模型并可输出 metrics.json
drone-detect         图片、目录或视频推理
drone-audit-data     数据集结构和标签质量审计
drone-check-metrics  指标门槛检查
drone-loop-report    生成单轮实验报告
drone-run-harness    编排 audit/train/val/gate/report 工作流
drone-demo-loop      生成无需真实数据/权重的 Harness/Loop demo
drone-compare-runs   比较两轮 run 并输出 loop 决策报告
```

示例：

```bash
drone-detect --model best.pt --source image.jpg
drone-detect --model best.pt --source images/ --classes 3 4 8
drone-val --model best.pt --metrics-output runs/harness/baseline/metrics.json
```

---

## 开发

```bash
make test      # 单元测试
make lint      # ruff 检查
make format    # black 检查
black .
```

完整贡献说明见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 复现基线

完整步骤见 [docs/reproducibility.md](docs/reproducibility.md)。

```bash
make convert
make train
make val
```

---

## 已知局限

- YOLOv8n 是最小变体；自行车、遮阳三轮车等小目标类别仍是主要误差来源。
- CPU 上仅跑 10 个 epoch；使用 GPU 并延长至 50-100 epoch 可显著提升检测表现。
- 当前使用 Ultralytics 默认增强策略，尚未针对小目标做专项优化。
- VisDrone 官方未公开测试集标注；本项目所有指标均基于 val 集。

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

VisDrone2019-DET 数据集有独立许可证，使用前请查阅 [aiskyeye.com](http://aiskyeye.com/)。YOLOv8 预训练权重遵循 [Ultralytics 许可证](https://github.com/ultralytics/ultralytics/blob/main/LICENSE)。
