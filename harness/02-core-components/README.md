# Harness Engineering — 核心组件详解

## 组件一：Prompt Engineering（提示工程）

Prompt 是 LLM 的"程序代码"。Harness 视角下的 Prompt 工程不只是写几句话，而是一套**可版本管理、可测试、可复用**的 Prompt 构建体系。

### System Prompt 的工程化

```
System Prompt 结构（工程化模板）
─────────────────────────────────────────
[角色定义]    你是一个 XX 助手，专门负责 XX
[能力边界]    你只能/不能做 XX
[输出格式]    请始终以 JSON 格式返回，字段包含 XX
[约束规则]    如果遇到 XX 情况，请回复 XX
[上下文注入]  {dynamic_context}  ← 运行时填充
```

### Few-shot 工程

Few-shot 示例不是随机挑选的，工程化的做法是：
- 维护一个**示例库（Example Store）**
- 根据当前 Query 动态检索最相关的示例（向量相似度）
- 控制示例数量不超过上下文窗口预算

### Prompt 版本管理

```
prompts/
├── v1/
│   ├── system.txt
│   └── user_template.txt
├── v2/
│   ├── system.txt        ← 修改了角色描述
│   └── user_template.txt
└── current -> v2/        ← 符号链接指向当前版本
```

像代码一样：PR Review → A/B 测试 → 灰度上线。

---

## 组件二：RAG（检索增强生成）

RAG 解决 LLM 的**知识截止**和**幻觉**问题，把"给 LLM 喂准确信息"变成一个工程系统。

### RAG 管道架构

```
离线阶段（Indexing Pipeline）
文档 → 分块（Chunking）→ 向量化（Embedding）→ 向量库

在线阶段（Query Pipeline）
用户问题 → 向量化 → 检索 Top-K → 重排序（Rerank）→ 注入 Prompt → LLM
```

### 关键工程决策

| 决策点 | 常见选项 | 影响 |
|--------|---------|------|
| 分块策略 | 固定 Token 数 / 语义分块 / 段落分块 | 检索精度 |
| Embedding 模型 | text-embedding-3 / BGE / E5 | 向量质量与成本 |
| 向量数据库 | Pinecone / Weaviate / pgvector | 延迟与规模 |
| 重排序 | Cohere Rerank / CrossEncoder | 精度提升但增加延迟 |
| 上下文窗口预算 | 给 RAG 结果留多少 Token | 与 Prompt 和历史对话竞争 |

### 常见失败模式

- **检索不相关**：查询和文档的语义空间不匹配，需要 Query 改写（HyDE）
- **上下文太长 LLM 忽略**：检索了 20 段但 LLM 只用了第 1 段，需要压缩或重排
- **分块破坏语义**：把一句话切断了，需要滑动窗口或语义分块

---

## 组件三：Guardrails（安全护栏）

Guardrails 是 Harness 的**安全层**，防止 LLM 的输出对系统或用户造成伤害。

### 护栏的分类

```
Input Guardrails（输入护栏）
├── Prompt Injection 检测     ← 防止用户劫持 System Prompt
├── 有害内容过滤               ← 拒绝处理涉暴、涉黄等输入
├── PII 检测                  ← 防止个人信息进入 LLM
└── 话题限制                   ← 客服机器人不回答竞品问题

Output Guardrails（输出护栏）
├── 格式验证                   ← 确保输出是合法的 JSON/XML
├── 幻觉检测                   ← 检查引用的事实是否在上下文中有据可查
├── 有害内容过滤               ← 防止输出有害建议
└── 敏感信息检测               ← 防止输出内部系统信息
```

### 工业界工具

| 工具 | 定位 |
|------|------|
| **NeMo Guardrails**（NVIDIA）| 对话流程护栏，用 Colang 声明式定义规则 |
| **Guardrails AI** | Python 库，定义输出 Schema 并验证 |
| **LlamaGuard**（Meta）| 专门训练的内容安全分类模型 |
| **Azure Content Safety** | 云服务，多模态内容审核 |
| **Perspective API**（Google）| 毒性检测 |

---

## 组件四：Structured Output（结构化输出）

让 LLM 输出**机器可直接解析的格式**，是工程化 LLM 的基础能力。

### 现代实现方式

```python
# 方式 1：JSON Mode（OpenAI / Anthropic 原生支持）
response = client.chat.completions.create(
    model="gpt-4o",
    response_format={"type": "json_object"},
    messages=[...]
)

# 方式 2：JSON Schema 约束（OpenAI Structured Outputs，2024.8）
from pydantic import BaseModel

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

response = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[...],
    response_format=CalendarEvent,  # 100% 保证符合 Schema
)
event = response.choices[0].message.parsed

# 方式 3：Function Calling / Tool Use
# LLM 决定何时调用哪个工具，参数严格符合 JSON Schema
```

### 工程价值

- 下游系统可以直接 `json.loads()` 而不需要复杂的解析逻辑
- 格式错误在 LLM 层就被拦截，不会传播到业务代码
- Schema 本身就是文档，便于团队协作

---

## 组件五：Evals（评估体系）

Evals 是 Harness Engineering 的**质量保证层**，相当于传统软件的测试套件，但针对 LLM 的非确定性特点设计。

### Evals 的层次

```
Level 1：代码级 Eval（确定性）
  ─ 正则匹配、JSON Schema 验证、关键词包含
  ─ 速度快，适合冒烟测试

Level 2：模型级 Eval（LLM-as-Judge）
  ─ 用另一个 LLM（通常是更强的）来评分
  ─ 适合评估"质量"、"相关性"、"有没有幻觉"

Level 3：人工 Eval
  ─ 最准确但最慢，用于建立 Ground Truth
  ─ 定期抽样，用于校准 Level 2 的评判模型

Level 4：在线 Eval（A/B 测试）
  ─ 通过用户行为指标（点赞、停留时长、转化率）反向衡量质量
```

### Eval 数据集工程

```
eval_suite/
├── golden_set/          ← 人工标注的高质量测试集，永久保留
│   ├── cases.jsonl
│   └── labels.jsonl
├── regression/          ← 每次发现的线上问题，加入防止回归
│   └── cases.jsonl
└── adversarial/         ← 专门设计的边界和对抗性用例
    └── cases.jsonl
```

### 工业界工具

| 工具 | 定位 |
|------|------|
| **OpenAI Evals** | 开源框架，定义和运行 LLM 评估 |
| **RAGAS** | 专门评估 RAG 系统质量（忠实度、相关性、召回率） |
| **DeepEval** | Python 测试框架，集成 CI/CD |
| **LangSmith**（LangChain）| 追踪 + Eval 一体化平台 |
| **Braintrust** | 企业级 Eval 平台，支持人工标注工作流 |
| **PromptFoo** | 开源 Prompt 测试和 Eval 工具 |
