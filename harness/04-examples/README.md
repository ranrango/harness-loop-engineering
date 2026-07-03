# Harness 示例说明

`harness_demo.py` 是一个无外部依赖的最小示例，演示 Harness Engineering 的四个基础能力。

## 运行方式

```bash
python3 harness/04-examples/harness_demo.py
```

脚本使用模拟 LLM 输出，不需要 API Key。

## 示例包含什么

| 模块 | 代码位置 | 说明 |
|---|---|---|
| Structured Output | `build_structured_prompt` / `parse_structured_output` | 把 JSON Schema 注入 Prompt，并从模型输出中解析 JSON |
| Guardrail | `OutputGuardrail` | 注册多个检查函数，对输出做 PII、长度等校验 |
| Eval | `EvalCase` / `run_eval_suite` | 用确定性规则评估模型输出是否通过 |
| Simple RAG | `SimpleRAGPipeline` | 演示文档索引、检索和 Prompt 构造流程 |

## 如何扩展到真实项目

### 1. Structured Output

演示代码用正则提取 JSON。生产环境建议优先使用模型原生的 JSON Schema、function calling 或 Pydantic 解析。

### 2. Guardrails

可以继续增加这些检查：

- 引用是否存在于 RAG context
- 是否包含客户 PII
- 是否输出内部密钥或系统路径
- 是否违反业务策略
- 是否触发敏感话题拒答

### 3. Evals

建议至少维护三类测试集：

- `golden_set`：人工标注的核心用例
- `regression_set`：线上失败案例沉淀
- `adversarial_set`：prompt injection、边界输入、格式破坏输入

### 4. RAG

演示代码用关键词重叠模拟检索。生产环境通常需要：

- 语义分块
- embedding
- 向量数据库
- rerank
- 来源引用
- 上下文预算管理

## 最小生产改造清单

- 给每个 Prompt 建版本号。
- 给每个输出建立 schema。
- 所有关键事实必须能追溯到 context 或工具返回。
- 每次改 Prompt/RAG/Guardrail 都运行 eval。
- 记录输入、输出、工具调用、失败原因和成本。
