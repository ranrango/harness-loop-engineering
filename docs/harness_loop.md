# Harness 与 Loop 工程化

本文说明本项目新增的实验线束和迭代闭环。

## 核心概念

Harness engineering 指把数据检查、训练、验证、指标门槛和报告产物统一到一份实验合约中。

Loop engineering 指把一次实验变成可重复闭环：数据审计 → 转换 → 训练 → 验证 → 指标门槛 → 报告 → 下一轮建议。

## 默认配置

默认实验配置位于：

```bash
configs/experiments/baseline_yolov8n.yaml
```

默认保持 CPU 安全，不要求 GPU。真实训练仍然需要本地准备 VisDrone2019-DET 数据集和依赖环境。

## 快速命令

数据审计：

```bash
make audit
```

打印完整闭环命令但不执行训练：

```bash
make harness-dry-run
```

检查 baseline 指标门槛：

```bash
make metrics-check
```

仅用已有权重验证：

```bash
python3 -m src.harness.runner \
  --config configs/experiments/baseline_yolov8n.yaml \
  --stage val \
  --skip-train \
  --model runs/detect/train/weights/best.pt
```

完整本地闭环：

```bash
python3 -m src.harness.runner \
  --config configs/experiments/baseline_yolov8n.yaml \
  --stage all
```

## 输出目录

Harness 输出位于：

```text
runs/harness/<experiment>/<timestamp>/
```

典型产物包括：

- `resolved_config.yaml`
- `audit.json`
- `commands.txt`
- `loop_report.md`
- `detect/`

这些产物属于运行输出，不提交进 Git。

生成 loop report 时可以直接指向一次 run 目录：

```bash
drone-loop-report \
  --config configs/experiments/baseline_yolov8n.yaml \
  --run-dir runs/harness/<experiment>/<timestamp>
```

`--run-dir` 会自动推导 `audit.json`、`metrics.json`、`commands.txt` 和 `loop_report.md` 的位置，并把 `resolved_config.yaml`、审计文件、指标文件、命令记录和报告文件列入报告的 Artifacts 区域。这样报告不仅说明指标是否过 gate，也能回答“这轮实验到底执行了哪些命令、留下了哪些证据”。

## 指标门槛

默认 gate 使用当前 README 中的 baseline 指标：

- precision: 0.354
- recall: 0.274
- mAP@0.5: 0.258
- mAP@0.5:0.95: 0.147

`allowed_drop: 0.02` 表示允许小幅波动。低于 `minimum - allowed_drop` 时，命令返回非零退出码。

## 需要用户提供的资源

实现和 CI 测试不需要额外资源。

真实训练或验证需要：

- VisDrone2019-DET 数据集，放在 README 约定的 `data/` 结构中。
- 已安装依赖的 Python 环境。
- 验证用 `best.pt`，或足够 CPU/GPU 时间重新训练。
