# Harness Loop 工程化实施计划

> **给 agentic worker：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务执行本计划。步骤使用 checkbox（`- [ ]`）语法追踪。

**目标：** 为 YOLOv8 VisDrone 项目加入配置驱动的实验 harness 和迭代 loop，同时保证 CI 不依赖真实数据、权重、GPU 或网络访问。

**架构：** 新增聚焦的 `src/harness/` 包，把配置解析、数据审计、指标门槛、报告渲染和运行编排拆到独立模块。现有 `drone-convert`、`drone-train`、`drone-val`、`drone-detect` 保持不变；harness 负责包裹这些流程，而不是替换它们。

**技术栈：** Python 3.9+、dataclasses、argparse、pathlib、json、subprocess、PyYAML、pytest、现有 Makefile 和 setuptools console scripts。

**逐行代码源：** 英文计划 [2026-07-04-harness-loop-engineering.md](/Users/randemac/Desktop/我的项目/drone-object-detection-main-clean/docs/superpowers/plans/2026-07-04-harness-loop-engineering.md) 保留完整代码块。本中文版本是执行说明和文档约定的中文版本；执行时如需复制完整 Python 文件内容，使用英文计划中同名任务的代码块。

**文档语言约定：** 从本计划之后，新建的用户可见项目文档默认使用中文优先；只有在发布、外部评审或明确需要时，再额外添加英文 companion。

---

## 文件地图

- 创建 `configs/experiments/baseline_yolov8n.yaml`：baseline 实验合约。
- 创建 `src/harness/__init__.py`：harness 包元数据。
- 创建 `src/harness/config.py`：类型化配置加载器和配置错误。
- 创建 `src/harness/audit_data.py`：数据审计逻辑、JSON/Markdown 渲染器和 CLI。
- 创建 `src/harness/metrics.py`：指标门槛逻辑、JSON 指标加载和 CLI。
- 创建 `src/harness/report.py`：loop report 渲染和基于规则的下一轮建议。
- 创建 `src/harness/runner.py`：dry-run 和真实运行编排 CLI。
- 创建 `tests/test_harness_config.py`：配置解析测试。
- 创建 `tests/test_harness_audit.py`：合成数据集审计测试。
- 创建 `tests/test_harness_metrics.py`：指标门槛测试。
- 创建 `tests/test_harness_report.py`：报告渲染测试。
- 创建 `tests/test_harness_runner.py`：runner dry-run 测试。
- 修改 `pyproject.toml`：添加 `PyYAML>=6.0` 和四个 console scripts。
- 修改 `Makefile`：添加 harness 快捷目标。
- 修改 `README.md`：添加简短 harness loop 章节，使用中文。
- 创建 `docs/harness_loop.md`：面向用户的中文指南。

## Task 1：实验配置和配置加载器

**文件：**
- 创建：`configs/experiments/baseline_yolov8n.yaml`
- 创建：`src/harness/__init__.py`
- 创建：`src/harness/config.py`
- 创建：`tests/test_harness_config.py`
- 修改：`pyproject.toml`

- [ ] **Step 1：先写失败测试**

创建 `tests/test_harness_config.py`。测试必须覆盖：

- `load_experiment_config("configs/experiments/baseline_yolov8n.yaml")` 能加载 baseline 配置。
- `config.experiment.name == "baseline_yolov8n"`。
- `config.data.root == Path("data")`。
- `config.data.splits == ["train", "val"]`。
- `config.model.weights == "yolov8n.pt"`。
- `config.train.epochs == 10`。
- `config.val.conf == 0.001`。
- `config.gates.map50_min == pytest.approx(0.258)`。
- `config.outputs.root == Path("runs/harness")`。
- 缺少 `data` section 时抛出 `ConfigError`，错误消息包含 `data`。
- `data.splits` 类型错误时抛出 `ConfigError`，错误消息包含 `data.splits`。

完整代码块见英文计划 Task 1 Step 1。

- [ ] **Step 2：运行测试确认失败**

运行：

```bash
python3 -m pytest tests/test_harness_config.py -q
```

预期：失败，因为 `src.harness.config` 和 baseline 配置还不存在。

- [ ] **Step 3：新增 baseline 实验 YAML**

创建 `configs/experiments/baseline_yolov8n.yaml`，包含：

- `experiment.name: baseline_yolov8n`
- `data.root: data`
- `data.dataset_yaml: data.yaml`
- `data.splits: [train, val]`
- `data.image_ext: jpg`
- `data.require_labels: true`
- `model.weights: yolov8n.pt`
- CPU 安全训练参数：`epochs=10`、`batch=8`、`imgsz=640`、`device=cpu`
- 验证参数：`conf=0.001`、`iou=0.6`
- gate：`map50_min=0.258`、`map_min=0.147`、`precision_min=0.354`、`recall_min=0.274`、`allowed_drop=0.02`
- `outputs.root: runs/harness`

完整 YAML 见英文计划 Task 1 Step 3。

- [ ] **Step 4：新增 harness 包初始化文件**

创建 `src/harness/__init__.py`，定义包说明和 `__version__ = "0.1.0"`。

完整代码块见英文计划 Task 1 Step 4。

- [ ] **Step 5：实现类型化配置加载器**

创建 `src/harness/config.py`。必须包含：

- `ConfigError`
- `ExperimentSection`
- `DataSection`
- `ModelSection`
- `TrainSection`
- `ValSection`
- `GatesSection`
- `OutputsSection`
- `ExperimentConfig`
- `load_experiment_config(path)`
- `_mapping`
- `_string`
- `_optional_string`
- `_string_list`
- `_bool`
- `_int`
- `_float`

实现要求：

- 使用 `yaml.safe_load`。
- 所有必填 section 和字段做显式类型校验。
- 路径字段转为 `Path`。
- `GatesSection.thresholds()` 返回 `precision`、`recall`、`map50`、`map` 四个阈值。
- 用户配置错误抛 `ConfigError`，消息里包含具体字段路径。

完整代码块见英文计划 Task 1 Step 5。

- [ ] **Step 6：添加 PyYAML 依赖**

修改 `pyproject.toml` 的 `dependencies`，加入：

```toml
"PyYAML>=6.0",
```

- [ ] **Step 7：运行配置测试**

运行：

```bash
python3 -m pytest tests/test_harness_config.py -q
```

预期：3 个测试通过。

- [ ] **Step 8：提交配置任务**

运行：

```bash
git add configs/experiments/baseline_yolov8n.yaml src/harness/__init__.py src/harness/config.py tests/test_harness_config.py pyproject.toml
git commit -m "feat: add harness experiment config"
```

## Task 2：数据审计

**文件：**
- 创建：`src/harness/audit_data.py`
- 创建：`tests/test_harness_audit.py`
- 修改：`pyproject.toml`

- [ ] **Step 1：先写数据审计测试**

创建 `tests/test_harness_audit.py`。测试必须覆盖：

- 合成 `VisDrone2019-DET-train/images` 和 `labels` 后，审计结果 `ok is True`。
- 正常样本中 `image_count == 1`、`label_count == 1`、`class_distribution == {3: 1}`。
- 图片缺少对应 label 时，`ok is False`，`missing_labels == ["orphan.txt"]`。
- YOLO 行中类别 ID 超出 0-9、坐标超出 0-1 或宽高非正时，会进入 `invalid_labels`。
- Markdown 渲染结果包含 `# Data Audit`、split 名称和 `PASS`。

完整代码块见英文计划 Task 2 Step 1。

- [ ] **Step 2：运行测试确认失败**

运行：

```bash
python3 -m pytest tests/test_harness_audit.py -q
```

预期：失败，因为 `src.harness.audit_data` 还不存在。

- [ ] **Step 3：实现数据审计模块和 CLI**

创建 `src/harness/audit_data.py`。必须包含：

- `SplitAudit`
- `DatasetAudit`
- `audit_dataset(config, data_root=None, splits=None)`
- `audit_to_dict(audit)`
- `render_audit_markdown(audit)`
- `_audit_split`
- `_collect_images`
- `_validate_yolo_row`
- `_issue`
- `parse_args`
- `main`

实现要求：

- 检查 split 目录、`images/`、按配置要求检查 `labels/`。
- 统计图片数、标签数、缺失标签、空标签、无效 YOLO 行、类别分布。
- JSON 输出用 `dataclasses.asdict`。
- Markdown 输出包含状态表和每个 split 的问题摘要。
- CLI 支持 `--config`、`--data-root`、`--format json|markdown`、`--output`。
- 审计通过退出 0，必需错误存在时退出 1。

完整代码块见英文计划 Task 2 Step 3。

- [ ] **Step 4：添加数据审计 CLI 入口**

修改 `pyproject.toml` 的 `[project.scripts]`，加入：

```toml
drone-audit-data = "src.harness.audit_data:main"
```

- [ ] **Step 5：运行数据审计测试**

运行：

```bash
python3 -m pytest tests/test_harness_audit.py -q
```

预期：4 个测试通过。

- [ ] **Step 6：提交数据审计任务**

运行：

```bash
git add src/harness/audit_data.py tests/test_harness_audit.py pyproject.toml
git commit -m "feat: add dataset audit harness"
```

## Task 3：指标门槛

**文件：**
- 创建：`src/harness/metrics.py`
- 创建：`tests/test_harness_metrics.py`
- 修改：`pyproject.toml`

- [ ] **Step 1：先写指标门槛测试**

创建 `tests/test_harness_metrics.py`。测试必须覆盖：

- baseline 指标 `precision=0.354`、`recall=0.274`、`map50=0.258`、`map=0.147` 通过 gate。
- 指标刚好下降 `allowed_drop=0.02` 仍然通过。
- `precision=0.20` 低于允许下降后失败，失败项名称为 `precision`。
- `load_metrics(path)` 能从 JSON 中读取指标。
- `render_gate_table(report)` 包含指标名和 `FAIL` 状态。

完整代码块见英文计划 Task 3 Step 1。

- [ ] **Step 2：运行测试确认失败**

运行：

```bash
python3 -m pytest tests/test_harness_metrics.py -q
```

预期：失败，因为 `src.harness.metrics` 还不存在。

- [ ] **Step 3：实现指标门槛模块和 CLI**

创建 `src/harness/metrics.py`。必须包含：

- `MetricGateResult`
- `MetricGateReport`
- `load_metrics(path)`
- `check_metric_gates(config, metrics)`
- `gate_report_to_dict(report)`
- `render_gate_table(report)`
- `parse_args`
- `main`

实现要求：

- 支持从 JSON 文件读取 `precision`、`recall`、`map50`、`map`。
- 支持 CLI 直接传 `--precision`、`--recall`、`--map50`、`--map`。
- required 值计算为 `minimum - allowed_drop`。
- 任一指标低于 required 时报告失败并返回非零退出码。
- `--json` 输出机器可读报告，否则输出 Markdown 表格。

完整代码块见英文计划 Task 3 Step 3。

- [ ] **Step 4：添加指标检查 CLI 入口**

修改 `pyproject.toml` 的 `[project.scripts]`，加入：

```toml
drone-check-metrics = "src.harness.metrics:main"
```

- [ ] **Step 5：运行指标测试**

运行：

```bash
python3 -m pytest tests/test_harness_metrics.py -q
```

预期：5 个测试通过。

- [ ] **Step 6：提交指标门槛任务**

运行：

```bash
git add src/harness/metrics.py tests/test_harness_metrics.py pyproject.toml
git commit -m "feat: add metric gate checks"
```

## Task 4：Loop Report

**文件：**
- 创建：`src/harness/report.py`
- 创建：`tests/test_harness_report.py`
- 修改：`pyproject.toml`

- [ ] **Step 1：先写报告测试**

创建 `tests/test_harness_report.py`。测试必须覆盖：

- 低召回率时，`suggest_next_experiments` 返回包含“召回率”的建议。
- 数据审计失败时，第一条建议以“先修复数据质量”开头。
- `render_loop_report(...)` 渲染结果包含：
  - `# Harness Loop Report`
  - `## Data Audit`
  - `## Metric Gates`
  - `## Next Experiments`

完整代码块见英文计划 Task 4 Step 1。

- [ ] **Step 2：运行测试确认失败**

运行：

```bash
python3 -m pytest tests/test_harness_report.py -q
```

预期：失败，因为 `src.harness.report` 还不存在。

- [ ] **Step 3：实现报告模块和 CLI**

创建 `src/harness/report.py`。必须包含：

- `LoopReportInput`
- `suggest_next_experiments(metrics, audit_ok)`
- `render_loop_report(data)`
- `parse_args`
- `main`
- `_audit_from_dict(raw)`

实现要求：

- 报告包含实验名、时间戳、数据审计、命令列表、指标表、gate 表、产物、风险、下一轮建议。
- 下一轮建议使用确定性规则，不调用 LLM 或外部服务。
- 数据质量失败时，优先建议修复数据。
- CLI 支持从 `audit.json`、`metrics.json` 渲染 Markdown 报告到 `--output`。

完整代码块见英文计划 Task 4 Step 3。

- [ ] **Step 4：添加报告 CLI 入口**

修改 `pyproject.toml` 的 `[project.scripts]`，加入：

```toml
drone-loop-report = "src.harness.report:main"
```

- [ ] **Step 5：运行报告测试**

运行：

```bash
python3 -m pytest tests/test_harness_report.py -q
```

预期：3 个测试通过。

- [ ] **Step 6：提交报告任务**

运行：

```bash
git add src/harness/report.py tests/test_harness_report.py pyproject.toml
git commit -m "feat: add loop report generation"
```

## Task 5：Harness Runner

**文件：**
- 创建：`src/harness/runner.py`
- 创建：`tests/test_harness_runner.py`
- 修改：`pyproject.toml`

- [ ] **Step 1：先写 runner dry-run 测试**

创建 `tests/test_harness_runner.py`。测试必须覆盖：

- `stage="all"` 且 `skip_train=True` 时，命令包含转换和验证，不包含 `src.train`。
- `stage="audit"` 时，只生成一个 `src.harness.audit_data` 命令，输出到 `run/audit.json`。
- `create_run_dir(config, outputs_root=tmp_path, timestamp="20260704_120000")` 创建 `tmp_path / "baseline_yolov8n" / "20260704_120000"`。

完整代码块见英文计划 Task 5 Step 1。

- [ ] **Step 2：运行测试确认失败**

运行：

```bash
python3 -m pytest tests/test_harness_runner.py -q
```

预期：失败，因为 `src.harness.runner` 还不存在。

- [ ] **Step 3：实现 runner 模块和 CLI**

创建 `src/harness/runner.py`。必须包含：

- `VALID_STAGES`
- `create_run_dir(config, outputs_root=None, timestamp=None)`
- `build_stage_commands(config, stage, run_dir, skip_train, model_path)`
- `run_harness(config_path, stage, dry_run, skip_train, model_path)`
- `parse_args`
- `main`

实现要求：

- 支持 `audit`、`convert`、`train`、`val`、`report`、`all`。
- 每次运行创建 `runs/harness/<experiment>/<timestamp>/`。
- 复制配置到 `resolved_config.yaml`。
- 把将要运行的命令写入 `commands.txt`。
- `--dry-run` 只打印命令，不执行训练或验证。
- `--skip-train` 时如果要验证，必须提供 `--model`。
- 真实运行时用 `subprocess.run(command, check=True)`。

完整代码块见英文计划 Task 5 Step 3。

- [ ] **Step 4：添加 runner CLI 入口**

修改 `pyproject.toml` 的 `[project.scripts]`，加入：

```toml
drone-run-harness = "src.harness.runner:main"
```

- [ ] **Step 5：运行 runner 测试**

运行：

```bash
python3 -m pytest tests/test_harness_runner.py -q
```

预期：3 个测试通过。

- [ ] **Step 6：提交 runner 任务**

运行：

```bash
git add src/harness/runner.py tests/test_harness_runner.py pyproject.toml
git commit -m "feat: add harness runner"
```

## Task 6：Makefile 和中文用户文档

**文件：**
- 创建：`docs/harness_loop.md`
- 修改：`README.md`
- 修改：`Makefile`

- [ ] **Step 1：添加 Makefile 目标**

修改 `Makefile` 顶部：

```make
PYTHON ?= python3
DATA_ROOT ?= data
HARNESS_CONFIG ?= configs/experiments/baseline_yolov8n.yaml

.PHONY: help install install-dev test lint format convert train val audit harness-dry-run metrics-check
```

在 `help` 中添加：

```make
	@echo "  audit        运行 harness 数据审计"
	@echo "  harness-dry-run  打印完整 harness 闭环命令但不训练"
	@echo "  metrics-check     使用命令行指标检查 baseline gate"
```

新增目标：

```make
audit:
	$(PYTHON) -m src.harness.audit_data --config $(HARNESS_CONFIG) --data-root $(DATA_ROOT)

harness-dry-run:
	$(PYTHON) -m src.harness.runner --config $(HARNESS_CONFIG) --stage all --dry-run --skip-train --model runs/detect/train/weights/best.pt

metrics-check:
	$(PYTHON) -m src.harness.metrics --config $(HARNESS_CONFIG) --precision 0.354 --recall 0.274 --map50 0.258 --map 0.147
```

- [ ] **Step 2：新增中文用户指南**

创建 `docs/harness_loop.md`。文档必须使用中文，并包含：

- `# Harness 与 Loop 工程化`
- 核心概念：Harness engineering 和 Loop engineering。
- 默认配置位置：`configs/experiments/baseline_yolov8n.yaml`。
- 快速命令：`make audit`、`make harness-dry-run`、`make metrics-check`。
- 仅用已有权重验证的命令。
- 完整本地闭环命令。
- 输出目录：`runs/harness/<experiment>/<timestamp>/`。
- 典型产物：`resolved_config.yaml`、`audit.json`、`commands.txt`、`loop_report.md`、`detect/`。
- 指标门槛解释。
- 需要用户提供的资源。

完整 Markdown 内容见英文计划 Task 6 Step 2。

- [ ] **Step 3：在 README 中添加中文章节**

在 `README.md` 的 Makefile 快捷命令块之后加入中文章节 `## Harness 与 Loop 工程化`，包含：

- 一句话解释轻量实验线束。
- `make audit`
- `make harness-dry-run`
- `make metrics-check`
- 默认配置位置。
- 指向 `docs/harness_loop.md` 的链接。

完整 Markdown 内容见英文计划 Task 6 Step 3。

- [ ] **Step 4：运行文档相关命令**

运行：

```bash
make metrics-check
```

预期：通过，并打印 Markdown 指标 gate 表。

运行：

```bash
python3 -m pytest tests/test_harness_config.py tests/test_harness_metrics.py -q
```

预期：通过。

- [ ] **Step 5：提交文档和 Makefile 任务**

运行：

```bash
git add Makefile README.md docs/harness_loop.md
git commit -m "docs: document harness loop workflow"
```

## Task 7：完整验证和收尾

**文件：**
- 只修改验证失败要求修复的文件。

- [ ] **Step 1：运行 harness 聚焦测试**

运行：

```bash
python3 -m pytest tests/test_harness_config.py tests/test_harness_audit.py tests/test_harness_metrics.py tests/test_harness_report.py tests/test_harness_runner.py -q
```

预期：所有 harness 测试通过。

- [ ] **Step 2：运行所有测试**

运行：

```bash
python3 -m pytest tests/ --tb=short -q
```

预期：原有 25 个测试和新增 harness 测试全部通过。

- [ ] **Step 3：运行 lint**

运行：

```bash
ruff check src/ scripts/ tests/
```

预期：无问题。

- [ ] **Step 4：运行格式检查**

运行：

```bash
black --check src/ scripts/ tests/
```

预期：所有检查文件无需改动。

- [ ] **Step 5：运行 dry-run smoke 命令**

运行：

```bash
python3 -m src.harness.runner --config configs/experiments/baseline_yolov8n.yaml --stage audit --dry-run
```

预期：通过；在被 `.gitignore` 忽略的 `runs/harness/` 下创建一个运行目录，打印 audit 命令，不训练。

- [ ] **Step 6：检查 git 状态**

运行：

```bash
git status --short
```

预期：只包含有意修改的 source、test、docs、config 和 `pyproject.toml` 文件。`runs/` 必须仍然被忽略。

- [ ] **Step 7：如验证修复产生改动，提交收尾调整**

如果 Step 1 到 Step 6 过程中确实修复了文件，运行：

```bash
git add configs/experiments/baseline_yolov8n.yaml src/harness tests Makefile README.md docs/harness_loop.md pyproject.toml
git commit -m "chore: verify harness loop workflow"
```

如果前面任务提交后没有新增改动，不创建空提交。

## 对照 Spec 的自检

- 实验 YAML 配置：Task 1 创建 `configs/experiments/baseline_yolov8n.yaml`。
- 数据审计和 JSON/Markdown 输出：Task 2 实现 `src/harness/audit_data.py`。
- runner stage 和 dry-run：Task 5 实现 `src/harness/runner.py`。
- 指标门槛：Task 3 实现 `src/harness/metrics.py`。
- loop report 和下一步建议：Task 4 实现 `src/harness/report.py`。
- 中文文档和 Makefile 快捷入口：Task 6 更新 README、Makefile，并新增 `docs/harness_loop.md`。
- 不依赖真实数据、权重、GPU 或网络的轻量测试：Task 1 到 Task 5 都使用合成数据和直接单元测试。
- 现有测试继续通过：Task 7 运行完整测试。

