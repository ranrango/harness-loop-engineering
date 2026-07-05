# 变更记录

本文件记录项目的重要变更，格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

## [未发布]

### 变更

- README 首页不再展示检测 baseline 的性能结果内容。
- README 明确说明检测 baseline 来源于 `ranrango/drone-object-detection`，本仓库侧重 Harness/Loop 工程化。
- README 新增数据契约审计、指标门槛、实验 dry-run 和 loop report 四个 Harness/Loop 示例。
- `drone-loop-report` 新增 `--run-dir` 入口，可自动读取单轮 run 的审计、指标、命令记录和默认产物。
- `drone-run-harness` 生成报告时会把 `commands.txt` 和关键 artifacts 传入 loop report，增强实验可追溯性。
- 新增 `drone-demo-loop` 和 `make demo-loop`，可在没有真实数据或权重时生成自包含 Harness/Loop demo run。
- 新增 `drone-compare-runs` 和 `make compare-runs`，用于比较两轮 run 的审计状态、指标 delta、命令记录和下一步 loop 决策。
- `drone-compare-runs` 新增 `--json-output`，可写出机器可读的跨轮指标 delta 和 loop 决策 JSON。
- `drone-demo-loop` 新增 `--profile baseline|improved|regressed`，便于无资源演示跨轮对比。
- CI 新增 Harness/Loop 示例验证 job，自动运行 demo run 生成、跨轮比较、Markdown 报告和 JSON 决策产物检查。

## [0.1.0] — 2026-07-05

### 新增

- 发布 Harness & Loop Engineering 知识库和可运行示例，覆盖概念、核心组件、行业实践和应用案例。
- 集成无人机目标检测工程：YOLOv8/VisDrone 训练、验证、推理、标注转换、基线结果和复现文档。
- 新增配置驱动的 `src/harness/` 工作流，支持数据审计、runner 编排、指标门槛、验证指标输出和 loop report。
- 新增中文优先文档：`docs/harness_loop.md`、中文设计规格、中文实施计划和 README 工作流说明。
- 新增 CI：Python 3.9、3.10、3.11 测试矩阵，ruff 检查和 black 格式检查。
- 新增 `v0.1.0` GitHub Release。

### 变更

- 将仓库 README 合并为 Harness/Loop 方法论与无人机检测工程的一体化入口。
- 将项目链接、贡献指南和仓库元数据更新到 `ranrango/harness-loop-engineering`。
- 固定 `black==24.8.0`，保持 Python 3.9 兼容并避免 CI 格式规则漂移。

### 修复

- 移除中文实施计划中的本机绝对路径链接，改为仓库内相对链接。
- 修复 editable install 的 setuptools build backend 配置。
- 持久化验证指标 JSON，供 harness report 和指标 gate 使用。
