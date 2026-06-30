# Harness Engineering — 工业界发展与实践

## 1. 发展历程

### 2020–2022：探索期——"能用就行"

GPT-3（2020）发布后，早期的 LLM 应用主要靠**精心手写 Prompt** 来让模型按预期工作。这个阶段：

- Prompt 写在代码字符串里，没有版本管理
- 没有系统性的评估，靠人工肉眼看结果
- 应用大多是演示级别（Demo），不在生产环境承载关键业务
- "Prompt Engineering" 作为独立词汇开始出现，但仍被很多工程师轻视

**代表事件**：
- 2020：OpenAI 发布 GPT-3 API，开放商业使用
- 2021：GitHub Copilot 内测，第一个大规模商用 LLM 产品
- 2022.3：InstructGPT 论文发表，RLHF 进入公众视野

### 2022–2023：爆发期——"怎么让它可靠"

ChatGPT（2022.11）的爆发让大量公司开始在生产环境部署 LLM 应用，**可靠性问题**随之暴露：

- 幻觉问题在客服、法律、医疗场景造成严重风险
- Prompt Injection 攻击成为安全威胁
- 输出格式不稳定导致下游系统崩溃
- 如何评估 LLM 质量成为行业痛点

这个阶段催生了 Harness Engineering 的核心组件：
- **LangChain**（2022.10）封装了 Prompt 模板、Chain、Memory
- **LlamaIndex**（2022.11）系统化了 RAG 管道
- **Guardrails AI**（2023.3）提出输出验证框架
- **OpenAI Function Calling**（2023.6）使结构化输出变得可靠

### 2023–2024：工程化期——"怎么做成产品"

行业从"能用"转向"工程化"，Harness Engineering 作为独立方向成形：

- **Evals 工程**独立成为专业方向，OpenAI、Anthropic 都开始公开谈论 Evals 的重要性
- **LLMOps 平台**涌现（LangSmith、Weights & Biases、Helicone、LangFuse），提供追踪、版本管理、Eval 一体化
- **Structured Output** 从技巧变成标准能力（OpenAI 在 2024.8 发布 JSON Schema 强制约束）
- **RAG 从简单的向量检索演进**到 Agentic RAG、GraphRAG、HyDE 等高级形态

**代表事件**：
- 2023.3：GPT-4 发布，LLM 能力质变
- 2023.6：OpenAI Function Calling，工具调用标准化
- 2024.4：Meta 发布 LlamaGuard，开源内容安全模型
- 2024.8：OpenAI Structured Outputs，100% JSON Schema 保证

### 2024–2026：成熟期——"Harness as Infrastructure"

Harness Engineering 正在从"每个公司自己摸索"走向**平台化和标准化**：

- 云厂商（AWS Bedrock Guardrails、Azure AI Content Safety、Google Vertex AI Grounding）直接在平台层提供 Harness 能力
- **Model Context Protocol（MCP）**（Anthropic，2024.11）试图标准化 LLM 与工具的连接方式
- Evals 与 CI/CD 深度集成，每次 Prompt 修改都触发自动评估流水线
- **AI Gateway**（如 Portkey、LiteLLM）在请求层统一做 Guardrails、缓存、路由、Observability

---

## 2. 工业界实践：公司案例

### OpenAI — 把 Evals 写进工程文化

OpenAI 内部把 **Evals 作为模型改进的核心飞轮**：
- 每次发现模型在某个场景的失败案例，立即写成 Eval 加入测试集
- 新版模型必须在所有历史 Eval 上不退步（回归测试）
- 2023 年开源了 [openai/evals](https://github.com/openai/evals) 框架，邀请社区共建测试集

**对行业的影响**：将"评估"从模糊的主观感受变成了可量化、可自动化的工程实践。

### Anthropic — Constitutional AI 与 Harness 深度融合

Anthropic 的 Constitutional AI（CAI）方法论本质上是**把护栏烧进模型**，而不只是在应用层加过滤器：
- 模型训练时就被灌输一套"宪法"（行为准则）
- Claude 的 System Prompt 机制（`<system>` 标签）使 Harness 的权限分层更清晰：系统提示 > 用户提示
- 2024.11 发布 MCP，试图用协议标准化 Tool Use 的 Harness

### Microsoft — Copilot Stack

微软把 Harness Engineering 系统化成一个**"Copilot Stack"**架构：

```
应用层：Copilot 前端（M365、GitHub、Teams）
          │
Harness层：Prompt 管理、内容过滤、RAG（Microsoft Fabric）
          │
模型层：Azure OpenAI Service + Phi 系列小模型
          │
基础设施：Azure AI Foundry（统一管理 Evals、Fine-tuning、部署）
```

**PromptFlow**（开源）是微软 Harness 工程实践的外化，支持可视化编排 Prompt 管道、内置 Eval 节点。

### Google — Grounding 即 RAG 的 Harness 化

Google 在 Gemini API 中提供 **Grounding with Google Search**，本质上是把 RAG 的 Harness 作为托管服务：
- 开发者不需要自己搭向量库，Google 直接用实时搜索结果做 Grounding
- 自动附上来源引用，减少幻觉，同时提供可验证性
- **Vertex AI Grounding** 则支持接入企业私有知识库

**Gemma + Responsible AI Toolkit**：在开源模型层面提供内置的 Guardrails 工具链。

### Salesforce — Einstein Copilot 的 Guardrails 实践

Salesforce 的 AI 产品在 CRM 场景面临严格的数据安全要求，他们的 Harness 实践重点在**权限对齐**：
- LLM 只能访问当前用户权限范围内的 Salesforce 数据（Row-Level Security 映射到 RAG 检索过滤）
- 输出中检测并脱敏 PII 信息
- 所有 LLM 调用通过 Einstein Trust Layer 审计，满足 GDPR/HIPAA

### 初创公司生态

| 公司 | 产品定位 | 解决的 Harness 问题 |
|------|---------|-------------------|
| **Guardrails AI** | 输出验证框架 | 结构化输出、内容护栏 |
| **Braintrust** | Eval 平台 | LLM 评估、人工标注工作流 |
| **LangSmith** | LLMOps 平台 | 追踪、Eval、Prompt 版本管理 |
| **Portkey** | AI Gateway | 统一 Guardrails、路由、缓存 |
| **PromptLayer** | Prompt 管理 | Prompt 版本控制、A/B 测试 |
| **Weights & Biases (Weave)** | ML + LLM 追踪 | 全链路 Observability |

---

## 3. 前沿方向

### 3.1 Agentic RAG

传统 RAG 是一次性检索。**Agentic RAG** 让 Agent 决定：
- 是否需要检索
- 检索哪个知识库
- 检索结果够不够，是否需要追加检索
- 如何综合多个来源的信息

代表实现：LlamaIndex Agentic RAG、LangChain Adaptive RAG。

### 3.2 GraphRAG

微软研究院提出（2024），用**知识图谱**代替纯向量检索，捕获文档间的结构化关系，在需要跨文档推理的复杂问答中比传统 RAG 准确率高 50%+。

### 3.3 Prompt Caching

Anthropic Claude（2024.8）和 OpenAI 相继支持 **Prompt Caching**：
- System Prompt 等静态内容在服务端缓存
- 重复请求只需传输动态部分
- 成本降低 90%，延迟降低 85%
- 这让"超长 System Prompt 作为知识库"的 Harness 模式变得经济可行

### 3.4 Multimodal Harness

随着 GPT-4o、Gemini 1.5、Claude 3.5 的多模态能力成熟，Harness 需要扩展到：
- 图像内容安全过滤
- 音频转写结果的验证
- 视频理解输出的 Structured Schema

### 3.5 Small Model + Harness > Large Model

行业发现：**一个被良好 Harness 约束的 7B 小模型**，在特定任务上可以超越没有 Harness 的 GPT-4：
- Fine-tuning 让小模型专注特定领域
- Structured Output + Guardrails 弥补小模型的不稳定性
- 成本是 GPT-4 的 1/100

这正在推动"**Harness-first，Model-agnostic**"的设计原则：先设计好 Harness，再选最合适的模型。

---

## 4. 工程师的角色演变

| 时间 | 角色 | 核心工作 |
|------|------|---------|
| 2022 以前 | ML 工程师 | 训练模型、调参 |
| 2022–2023 | Prompt 工程师 | 写 Prompt、调教模型 |
| 2023–2024 | LLM 应用工程师 | 搭 RAG、写 Chain、接 API |
| 2024–2026 | **Harness Engineer** | 系统设计 Prompt 体系、Evals 流水线、Guardrails 框架、LLM Observability |

Harness Engineer 是当前 AI 应用团队中最稀缺的角色之一，要求同时具备：
- LLM 原理理解（知道为什么会幻觉、为什么 Prompt 有效）
- 软件工程能力（设计可维护的 Harness 系统）
- 数据能力（构建 Eval 数据集，分析模型行为）
