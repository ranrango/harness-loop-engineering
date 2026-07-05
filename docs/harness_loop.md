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

## 自包含 Demo

如果还没有 VisDrone 数据集或模型权重，可以先生成一个只用于 Harness/Loop 演示的 synthetic run：

```bash
drone-demo-loop --profile baseline
# 或
make demo-loop
```

该命令会写入 `runs/harness-demo/harness_loop_demo/<timestamp>/`，包含：

- `resolved_config.yaml`
- `demo_data/`
- `audit.json`
- `metrics.json`
- `commands.txt`
- `loop_report.md`

这个 demo 不训练模型，也不声明检测精度；它只演示一次闭环实验应该留下哪些可审计证据，以及 loop report 如何把数据审计、指标 gate、命令记录和下一轮建议串起来。

`--profile` 可取 `baseline`、`improved`、`regressed`，用于构造不同指标走势的 synthetic run。

## 跨轮对比

Loop Engineering 的关键不是只看单轮结果，而是比较上一轮和候选轮的变化。可以用 demo profile 生成两轮 run：

```bash
drone-demo-loop --profile baseline --timestamp baseline
drone-demo-loop --profile improved --timestamp improved
drone-compare-runs \
  --base-run runs/harness-demo/harness_loop_demo/baseline \
  --candidate-run runs/harness-demo/harness_loop_demo/improved
```

`drone-compare-runs` 会读取两次 run 的 `audit.json`、`metrics.json` 和 `commands.txt`，输出：

- 数据审计是否从 PASS 变成 FAIL。
- `precision`、`recall`、`map50`、`map` 的 base/candidate/delta/status。
- 候选 run 的命令记录。
- 下一步 loop 决策建议，例如提升为下一轮 baseline、回滚复查或继续收集失败样本。

该比较同样适用于真实 `drone-run-harness` 产生的 run 目录。

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
CI 会运行 self-contained demo run 和跨轮 compare report 检查，用 synthetic 数据验证 Harness/Loop 示例链路；不会下载 VisDrone、模型权重或执行真实训练。

真实训练或验证需要：

- VisDrone2019-DET 数据集，放在 README 约定的 `data/` 结构中。
- 已安装依赖的 Python 环境。
- 验证用 `best.pt`，或足够 CPU/GPU 时间重新训练。
