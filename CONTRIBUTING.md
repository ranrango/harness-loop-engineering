# 贡献指南

感谢你考虑为本项目贡献代码或文档。

## 环境准备

```bash
git clone https://github.com/ranrango/harness-loop-engineering
cd harness-loop-engineering
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## 运行测试

```bash
make test
# 或直接运行：
pytest tests/ --tb=short
```

测试不依赖 torch 或 ultralytics，只需标准库和 pytest，覆盖转换逻辑、图片头解析、命令行参数解析和工具函数。

## 代码检查与格式化

```bash
make lint      # ruff 检查
make format    # black 格式检查（只读）
```

自动修复格式：`black .`

## 分支命名规范

| 用途 | 格式 |
|---|---|
| 新功能 | `feat/简短描述` |
| 缺陷修复 | `fix/简短描述` |
| 实验 | `experiment/描述` |
| 文档 | `docs/简短描述` |

## Pull Request 规范

1. 每个 PR 只做一件事。
2. 提交前确保所有测试通过。
3. 在 `CHANGELOG.md` 的 `[未发布]` 下记录所有用户可见的变更。
4. 不要提交数据集、模型权重、训练输出或凭据文件。

## 不应提交的内容

详见 `.gitignore`，特别注意：

- `data/` — VisDrone 数据集（单独下载）
- `runs/` — 训练和验证输出
- `*.pt`、`*.pth` — 模型权重
- `.env`、`*.key` — 凭据文件

## 提交 Issue

请在 https://github.com/ranrango/harness-loop-engineering/issues 提交问题，并包含：
- Python 版本和操作系统
- 复现步骤
- 预期行为与实际行为
