# Harness & Loop Engineering — AI 应用开发工程指南

> **Harness Engineering（驾驭工程）** 和 **Loop Engineering（循环工程）** 是 2025–2026 年 AI 应用开发领域的两个核心工程方向，描述了如何系统性地构建可控、可靠、可持续演进的 AI 应用。

---

## 什么是这两个概念？

| | Harness Engineering | Loop Engineering |
|---|---|---|
| **中文** | 驾驭工程 | 循环工程 |
| **核心问题** | 如何让 LLM 可控、可预测地完成任务 | 如何构建 AI Agent 的感知-推理-行动闭环 |
| **关键词** | Prompt 工程、Guardrails、Evals、RAG、Tool Use | ReAct、Agent Loop、RLHF、Human-in-the-Loop |
| **终极目标** | 把不可控的 LLM "驾驭"成可靠的业务组件 | 让 Agent 通过反馈不断自我改进 |

---

## 目录结构

```
harness-loop-engineering/
├── PRACTICAL_GUIDE.md          # 从概念到落地的实践手册
├── applications/               # 行业应用案例
├── harness/                    # 驾驭工程
│   ├── 01-concepts/            # 核心概念：什么是 Harness Engineering
│   ├── 02-core-components/     # 核心组件详解
│   ├── 03-industry/            # 工业界现状与发展
│   └── 04-examples/            # 实际代码示例
└── loop/                       # 循环工程
    ├── 01-concepts/            # 核心概念：什么是 Loop Engineering
    ├── 02-core-components/     # 核心组件详解
    ├── 03-industry/            # 工业界现状与发展
    └── 04-examples/            # 实际代码示例
```

---

## 快速导航

### Harness Engineering

| 章节 | 内容 |
|------|------|
| [实践手册](./PRACTICAL_GUIDE.md) | 如何把 Harness 与 Loop 落到真实 AI 应用 |
| [应用案例](./applications/) | 客服、代码、工业、研究等场景的组合设计 |
| [核心概念](./harness/01-concepts/) | 定义、起源、与传统工程的关系 |
| [核心组件](./harness/02-core-components/) | Prompt 工程、Guardrails、Evals、RAG、Tool Use |
| [工业界现状](./harness/03-industry/) | 发展历程、各公司实践、前沿趋势 |
| [代码示例](./harness/04-examples/) | 可运行的工程实践示例 |

### Loop Engineering

| 章节 | 内容 |
|------|------|
| [核心概念](./loop/01-concepts/) | 定义、起源、Agent Loop 心智模型 |
| [核心组件](./loop/02-core-components/) | ReAct、Memory、Planning、Multi-Agent |
| [工业界现状](./loop/03-industry/) | 发展历程、各公司实践、前沿趋势 |
| [代码示例](./loop/04-examples/) | 可运行的 Agent Loop 示例 |

---

## 两者的关系

```
                    ┌─────────────────────────────┐
                    │      AI 应用系统               │
                    │                             │
   Harness ────────▶│  约束 · 驱动 · 评估 LLM       │
   Engineering      │                             │
                    │  ┌─────────────────────┐    │
   Loop  ──────────▶│  │  Agent 感知→推理→行动  │    │
   Engineering      │  │  ←─── 反馈闭环 ────   │    │
                    │  └─────────────────────┘    │
                    └─────────────────────────────┘
```

**Harness 是基础设施层**（怎么让 LLM 可靠工作），**Loop 是执行逻辑层**（Agent 如何在 Harness 之上循环行动）。一个好的 AI 应用，两者缺一不可。

---

## 从概念到落地

构建真实 AI 应用时，建议按下面的顺序推进：

1. **先建 Harness**：明确模型角色、上下文来源、工具权限、输出格式、安全护栏和评估集。
2. **再建 Loop**：定义触发条件、任务规划、工具调用、观察反馈、循环内评估、修复策略和停止条件。
3. **最后接业务系统**：接入工单、CI、知识库、告警、审批流、监控和日志。

最小生产闭环可以理解为：

```
输入/事件
  ↓
Harness: Prompt + RAG + Tool Schema + Guardrails + Evals
  ↓
Loop: Plan/ReAct -> Act -> Observe -> Verify -> Repair/Stop
  ↓
业务结果: 答复、草稿、PR、工单、报告、告警升级
```

更多设计模板见 [实践手册](./PRACTICAL_GUIDE.md)。

---

## 推荐阅读顺序

1. 先读 Harness 概念 → 理解为什么 LLM 需要被"驾驭"
2. 再读 Loop 概念 → 理解 Agent 如何在约束下持续运行
3. 对照工业界章节 → 看真实公司怎么做
4. 阅读实践手册 → 学会设计真实系统
5. 跑通代码示例 → 动手实践
6. 对照应用案例 → 迁移到自己的业务场景

---

## 仓库适合谁

- 想把 ChatGPT/Claude/Gemini/OpenAI API 做成生产级应用的开发者
- 正在搭 RAG、Agent、LLMOps、AI Gateway、企业 Copilot 的工程团队
- 想理解 Prompt Engineering 之后下一层工程能力的人
- 需要评估 AI Agent 安全性、可靠性和工业落地路径的产品/技术负责人
