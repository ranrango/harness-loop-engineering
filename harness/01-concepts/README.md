# Harness Engineering — 核心概念

## 1. 什么是 Harness Engineering？

Harness，英文原意是**驾驭马匹的缰绳与挽具**。Harness Engineering 借用这个比喻，描述一套工程实践体系：

> **把强大但难以控制的 LLM，通过一系列约束、引导和验证机制，变成可预测、可靠、可集成到业务系统的组件。**

LLM 本身像一匹能力极强但不稳定的马——它可能跑偏、幻觉、越权、输出格式混乱。Harness Engineering 就是给这匹马装上缰绳和挽具。

---

## 2. 为什么需要 Harness Engineering？

### LLM 的天然缺陷

```
问题                          表现
─────────────────────────────────────────────────────────────
不确定性（Non-deterministic）  同一个 Prompt 多次运行，结果可能不同
幻觉（Hallucination）         编造不存在的事实、引用、API 调用
越界（Boundary violation）    不该说的说了，不该做的做了
格式不可控                    你要 JSON，它给你 JSON 加一段解释文字
知识截止（Knowledge cutoff）  不知道最新信息
上下文窗口限制                 超长文档无法一次处理
```

### 工程的责任

这些缺陷不能靠"换一个更好的模型"来完全解决——它们是**语言模型的基本属性**。Harness Engineering 的任务是在应用层对这些缺陷建立防线：

```
用户请求
   │
   ▼
[Input Harness]  ← 输入验证、Prompt 构造、上下文注入
   │
   ▼
  LLM
   │
   ▼
[Output Harness] ← 输出解析、格式验证、安全过滤、Eval 评分
   │
   ▼
业务系统
```

---

## 3. 核心思想：约束即能力

传统软件工程里，约束（类型系统、接口契约）让代码更可靠。Harness Engineering 把同样的思想应用到 LLM：

| 传统软件工程 | Harness Engineering |
|------------|-------------------|
| 类型系统约束输入输出 | Structured Output 约束 LLM 输出为 JSON Schema |
| 单元测试验证函数行为 | Evals 验证 LLM 在各种场景下的表现 |
| 权限系统限制操作范围 | Guardrails 限制 LLM 的行为边界 |
| API 契约定义接口 | System Prompt 定义 LLM 的角色和职责 |
| 监控告警 | LLM Observability（追踪每次调用的输入输出和延迟） |

---

## 4. 五大核心组件

```
┌──────────────────────────────────────────────────────┐
│                  Harness Engineering                  │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐ │
│  │  Prompt  │  │   RAG    │  │      Tool Use       │ │
│  │  工程     │  │  知识增强  │  │    工具调用          │ │
│  └──────────┘  └──────────┘  └─────────────────────┘ │
│                                                      │
│  ┌──────────────────────┐  ┌─────────────────────┐   │
│  │      Guardrails      │  │        Evals        │   │
│  │      安全护栏         │  │      评估体系        │   │
│  └──────────────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

详见 [02-core-components](../02-core-components/)。

---

## 5. 与相关概念的区分

| 概念 | 关系 |
|------|------|
| **Prompt Engineering** | Harness 的子集，只关注 Prompt 设计 |
| **MLOps** | 关注模型训练/部署，Harness 关注模型使用 |
| **LLMOps** | 更接近，但 LLMOps 更强调运维，Harness 更强调工程控制 |
| **AI Safety** | Harness 的安全护栏部分与 AI Safety 有重叠，但 Harness 聚焦应用层 |
| **Loop Engineering** | Harness 是基础设施，Loop 是在 Harness 上运行的 Agent 执行逻辑 |

---

## 6. 一句话理解

> Harness Engineering = 让 LLM 从"实验室里的黑盒"变成"生产环境里可信赖的工程组件"的全套方法论。
