# Harness 与 Loop 工程化设计

日期：2026-07-04
项目：`drone-object-detection-main-clean`

## 目标

这个项目已经具备一个清晰的 YOLOv8 基线：标注转换、训练、验证、推理、测试、
Makefile 目标、CI 和复现说明都已经存在。下一步不是再堆一组零散命令，而是把
项目改造成更容易持续迭代的工程系统。

本设计加入两层能力：

- Harness engineering：为数据检查、训练、验证、指标门槛和报告产物建立标准实验合约。
- Loop engineering：建立从数据审计到实验运行，再到指标复盘和下一轮建议的可重复闭环。

实现时不能把数据集、模型权重、凭据或训练输出提交进 Git。CI 必须保持轻量，
不依赖 VisDrone、YOLO 权重、GPU 或网络下载。

## 选定方案

采用配置驱动的轻量 MLOps 闭环。

未采用的方案：

- 最小脚本方案：加入速度最快，但实验仍然太随意，后续难以比较和复盘。
- 完整平台方案：接入 MLflow、DVC、W&B 或远程 runner 后会更专业，但当前阶段过重，
  还会要求额外服务和用户资源。

选定方案会新增本地、可测试的 Python 模块和 CLI 入口。它保持现有项目风格，
不替换已有命令。

## 范围

本阶段包含：

- 实验 YAML 配置。
- 面向 VisDrone 目录和 YOLO 标签输出的数据审计。
- 编排已有转换、训练、验证和报告步骤的 harness runner。
- 基于 baseline 或配置阈值的指标门槛检查。
- 带下一步建议的 loop report 生成。
- 文档和 Makefile 快捷入口。
- 不依赖真实数据集或模型权重的单元测试。

本阶段不包含：

- 自动下载 VisDrone。
- 提交真实数据、权重或训练输出。
- 在 CI 中运行真实训练。
- 新增 Web dashboard。
- 接入外部实验追踪服务。

## 架构

新增包：

```text
src/harness/
  __init__.py
  config.py
  audit_data.py
  metrics.py
  report.py
  runner.py
```

新增配置和文档：

```text
configs/experiments/baseline_yolov8n.yaml
docs/harness_loop.md
```

新增测试：

```text
tests/test_harness_config.py
tests/test_harness_audit.py
tests/test_harness_metrics.py
tests/test_harness_report.py
```

新增命令行入口：

```text
drone-audit-data
drone-run-harness
drone-check-metrics
drone-loop-report
```

已有命令保持不变：

- `drone-convert`
- `drone-train`
- `drone-val`
- `drone-detect`

新的 harness 会调用或镜像这些流程，避免重复实现 YOLO 专属行为。

## 实验配置

`configs/experiments/baseline_yolov8n.yaml` 定义一份实验合约：

```yaml
experiment:
  name: baseline_yolov8n
  description: YOLOv8n VisDrone baseline loop

data:
  root: data
  dataset_yaml: data.yaml
  splits: [train, val]
  image_ext: jpg
  require_labels: true

model:
  weights: yolov8n.pt

train:
  enabled: true
  epochs: 10
  batch: 8
  imgsz: 640
  device: cpu
  workers: 4
  patience: 50

val:
  enabled: true
  batch: 8
  imgsz: 640
  device: cpu
  conf: 0.001
  iou: 0.6

gates:
  map50_min: 0.258
  map_min: 0.147
  precision_min: 0.354
  recall_min: 0.274
  allowed_drop: 0.02

outputs:
  root: runs/harness
```

解析器应尽量使用标准库。如果 YAML 解析确实需要 PyYAML，可以把它作为小依赖加入。
实现时要保持 schema 明确：必填字段缺失或类型不正确时，给出可操作的错误信息。

## 数据审计

`drone-audit-data` 用来检查本地数据集是否已经准备好进入闭环。

输入：

- `--config configs/experiments/baseline_yolov8n.yaml`
- 可选 `--data-root`
- 可选 `--format json|markdown`
- 可选 `--output path`

检查项：

- 预期 split 目录是否存在。
- 每个 split 是否存在 `images/`。
- 需要原始 VisDrone 标注时，是否存在 `annotations/`。
- 要求转换后标签时，是否存在 `labels/`。
- 每个 split 的图片数量和标签数量。
- 图片是否缺少对应标签。
- 是否存在空标签文件。
- 是否存在无效 YOLO 行：列数错误、非数值、类别 ID 超出 0-9、归一化坐标超出 0-1、
  宽高非正数。
- 标签文件中的类别分布。

输出：

- 面向自动化的 JSON 摘要。
- 面向人工阅读的 Markdown 摘要。

退出行为：

- 数据集通过必需检查时退出码为 0。
- 必需目录缺失或发现无效标签时返回非零退出码。
- 空标签等警告应被报告，并允许配置为非致命问题。

## Harness Runner

`drone-run-harness` 是一次实验闭环的统一入口。

输入：

- `--config configs/experiments/baseline_yolov8n.yaml`
- `--stage audit|convert|train|val|report|all`
- `--dry-run`
- `--skip-train`
- `--model path/to/best.pt`

行为：

1. 加载并校验实验配置。
2. 在 `runs/harness/<experiment>/<timestamp>/` 下创建带时间戳的运行目录。
3. 将解析后的配置复制到运行目录。
4. 运行数据审计。
5. 按需将原始 VisDrone 标注转换为 YOLO 标签。
6. 按需通过现有 `src.train` 流程训练。
7. 使用现有 `src.val` 流程或用户提供的模型路径验证。
8. 检查指标门槛。
9. 生成 loop report。

第一版实现可以通过 subprocess 调用现有 CLI 入口，以便尽量贴近当前行为。
共享的纯逻辑应放在小函数中，方便单元测试。

## 指标门槛

`drone-check-metrics` 将观测指标与配置阈值进行比较。

输入：

- `--config configs/experiments/baseline_yolov8n.yaml`
- `--metrics path/to/metrics.json`
- 可选直接传值：`--map50`、`--map`、`--precision`、`--recall`

指标：

- `precision`
- `recall`
- `map50`
- `map`

门槛行为：

- 每个已配置指标在应用 `allowed_drop` 后仍高于或等于最低值，则通过。
- 任一指标低于门槛时，输出清晰的逐指标表格。
- 门槛失败时返回非零退出码，便于本地自动化使用。

检查器应同时支持当前 baseline 值和未来不同实验的阈值文件。

## Loop Report

`drone-loop-report` 为每次迭代生成 Markdown 报告。

报告章节：

- 实验身份和时间戳。
- 数据审计摘要。
- 训练和验证命令摘要。
- 带通过/失败状态的指标表。
- 产物位置。
- 已观察到的风险和缺失资源。
- 下一轮实验建议。

下一轮建议在本阶段应是确定性的、基于规则的，例如：

- 召回率低：尝试降低置信度阈值、增加 epoch、增大图片尺寸或检查类别不平衡。
- 精确率低：检查误检样本并提高置信度阈值。
- 小目标类别弱：增大图片尺寸或加入有针对性的增强。
- 标签缺失或框无效：先修复转换和数据质量，再训练。

本阶段不需要 LLM API 或外部服务。

## 错误处理

错误信息应具体且可操作：

- 数据根目录缺失：说明缺失路径，并提示如何创建预期目录结构。
- 标签缺失：建议运行 `drone-convert`。
- 验证缺少模型：建议使用 `--model path/to/best.pt` 或先运行训练。
- 配置无效：包含字段名和预期类型。
- 指标门槛失败：打印具体指标、观测值、要求值和差距。

命令应避免在预期的用户错误上直接抛出堆栈。开发中的未知错误可以正常暴露。

## 测试

测试必须保持轻量。

新增单元测试覆盖：

- 加载有效实验配置。
- 拒绝缺少必填字段的配置。
- 审计一个极小的合成 VisDrone 风格目录。
- 检测缺失标签和无效 YOLO 行。
- 指标门槛通过和失败。
- 渲染包含所有必需章节的 loop report。

不要在 CI 中测试真实 YOLO 训练、真实 VisDrone 数据、下载权重或 GPU 执行。

现有测试必须继续通过：

```bash
python3 -m pytest tests/ --tb=short -q
```

实现后的推荐验证命令：

```bash
make test
make lint
make format
```

## 文档

更新 README，并新增 `docs/harness_loop.md`，包含：

- 本项目中 harness engineering 的含义。
- 本项目中 loop engineering 的含义。
- 数据审计、dry-run、仅验证和完整本地闭环的快速命令。
- 真实训练所需资源。
- 预期输出目录。
- 如何理解指标门槛失败。

文档应保持中英友好，以简洁中文说明为主，风格贴近当前 README。

## 资源需求

实现和 CI 测试不需要额外资源。

如果要运行真实闭环，用户需要提供：

- 按文档中 `data/` 结构放置的 VisDrone2019-DET 数据集。
- 已安装项目依赖的本地 Python 环境。
- 用于仅验证闭环的已训练 `best.pt`，或足够的 CPU/GPU 时间来训练。

GPU 是可选项。默认配置保持 CPU 安全，和当前 baseline 一致。

## 成功标准

完成条件：

- 项目中有已提交的实验配置。
- 新 harness CLI 通过 `pyproject.toml` 安装。
- 合成数据集审计可以在测试中运行。
- 指标门槛可以确定性地通过和失败。
- 不依赖真实数据或 YOLO 权重也能生成 loop report。
- README 或文档解释完整闭环。
- 现有测试和新增测试在本地通过。

